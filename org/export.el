;;; export.el --- org-publish handbook to HTML  -*- lexical-binding: t -*-
;; Usage from the github.io root: emacs --batch -l org/export.el
;;
;; Batch highlighting is engrave-faces (preset CSS), not htmlize.
;; htmlize needs a live display; this is the vault's org-export-config.el path.

(require 'package)
(package-initialize)
(let ((emacs-dir (or (getenv "EMACSDIR")
                     (expand-file-name "~/.config/emacs"))))
  (dolist (dir (list
                (expand-file-name "elpa/htmlize-20250724.1703" emacs-dir)
                (expand-file-name ".local/straight/build-30.2/htmlize" emacs-dir)
                (expand-file-name ".local/straight/repos/htmlize" emacs-dir)
                (expand-file-name ".local/straight/build-30.2/engrave-faces" emacs-dir)
                (expand-file-name ".local/straight/repos/engrave-faces" emacs-dir)))
    (when (file-directory-p dir)
      (add-to-list 'load-path dir))))
(require 'org)
(require 'ox-html)
(require 'ox-publish)
(require 'htmlize)
(require 'engrave-faces)
(require 'engrave-faces-html)

(setq engrave-faces-html-output-style 'preset
      org-html-htmlize-output-type 'css
      org-html-head-include-default-style nil
      org-html-head-include-scripts nil
      org-html-validation-link nil
      org-html-doctype "html5"
      org-html-html5-fancy t
      org-html-prefer-user-labels t
      org-html-link-org-files-as-html t
      org-export-with-section-numbers nil
      org-export-with-toc nil
      org-export-with-author nil
      org-export-with-timestamps nil
      org-export-with-drawers nil
      org-export-with-broken-links 'mark
      org-confirm-babel-evaluate nil
      ;; A clock in the head comment would change on every publish, so the
      ;; generated handbook would never match the tree. The comment is not shown.
      org-export-time-stamp-file nil)

(defun ljos-html-fontify-code-engrave (code lang)
  "Fontify CODE in LANG with engrave-faces so --batch has faces."
  (if (not lang)
      (org-html-encode-plain-text code)
    (let ((lang-mode (org-src-get-lang-mode lang)))
      (if (not (functionp lang-mode))
          (org-html-encode-plain-text code)
        (with-temp-buffer
          (insert code)
          (funcall lang-mode)
          (font-lock-ensure)
          (let ((result-buf (engrave-faces-html-buffer)))
            (prog1 (with-current-buffer result-buf (buffer-string))
              (kill-buffer result-buf))))))))

(advice-add 'org-html-fontify-code :override #'ljos-html-fontify-code-engrave)

(defun ljos-src-keep-code-element (html)
  "Keep <code> inside <pre class=\"src\">.
Org 9.5 wrote that wrapper and the published handbook still has it.
site.css sets pre code { font-size: inherit }, so the element does not
change the block a visitor sees. Org 9.6 omits it, which would rewrite
argv blocks on publish. Add the wrapper only when this Org left it out."
  (if (or (not (stringp html))
          (string-match "<pre class=\"src src-[^\"]+\"[^>]*><code>" html))
      html
    (replace-regexp-in-string
     "\\(<pre class=\"src src-[^\"]+\"[^>]*>\\)\\(\\(?:.\\|\n\\)*?\\)\\(</pre>\\)"
     "\\1<code>\\2</code>\\3"
     html)))

(advice-add 'org-html-src-block :filter-return #'ljos-src-keep-code-element)

(defun ljos-read-template (name)
  (let ((path (expand-file-name name
                                (expand-file-name "org/templates"
                                                  default-directory))))
    (with-temp-buffer
      (insert-file-contents path)
      (buffer-string))))

;; Site CSS owns colour. The engrave-faces preset is a light theme and
;; must not be concatenated here: it paints .ef-* black-on-white over
;; the dark handbook.
(setq org-html-head (ljos-read-template "head.html")
      org-html-preamble (ljos-read-template "nav.html")
      org-html-postamble (ljos-read-template "footer.html"))

;; The published handbook spells an en dash with the named reference.
;; Org's default table uses the numeric form of the same character,
;; which would rewrite the Notes list on every build.
(setq org-html-special-string-regexps
      '(("\\\\-" . "&#x00ad;")
        ("---\\([^-]\\)" . "&#x2014;\\1")
        ("--\\([^-]\\)" . "&ndash;\\1")
        ("\\.\\.\\." . "&#x2026;")))

(defconst ljos-site-origin "https://leidarljos.github.io"
  "Public origin. Canonical URLs are absolute so a redirect stub and the
page it names do not depend on which host served the file.")

(defvar ljos-site-root (expand-file-name default-directory)
  "Site root, captured when this file loads.
The export filter runs with default-directory set to the Org source
directory, so a canonical path cannot use that later value.")

(defun ljos-html-escape-attr (text)
  "Escape TEXT for a double-quoted HTML attribute."
  (dolist (pair '(("&" . "&amp;")
                  ("<" . "&lt;")
                  (">" . "&gt;")
                  ("\"" . "&quot;"))
                 text)
    (setq text (replace-regexp-in-string (car pair) (cdr pair) text t t))))

(defun ljos-canonical-url (output-file)
  "Absolute URL for OUTPUT-FILE.
A directory index is the directory itself, with a trailing slash, which
is how the docs pages already publish their canonical link."
  (let* ((file (if (file-name-absolute-p output-file)
                   output-file
                 (expand-file-name output-file ljos-site-root)))
         (rel (file-relative-name file ljos-site-root)))
    (setq rel (replace-regexp-in-string "\\`\\./" "" rel))
    (cond
     ((string-equal rel "index.html") (concat ljos-site-origin "/"))
     ((string-suffix-p "/index.html" rel)
      (concat ljos-site-origin "/"
              (substring rel 0 (- (length rel) (length "index.html")))))
     (t (concat ljos-site-origin "/" rel)))))

(defun ljos-inject-canonical (output backend info)
  "Add this file's canonical URL and og:title.
og:image is the one site preview in org/templates/head.html. The title
is the Org title, which is also the document title."
  (if (not (and (org-export-derived-backend-p backend 'html)
                (plist-get info :output-file)))
      output
    (let* ((title (org-trim (org-export-data (plist-get info :title) info)))
           (canon (ljos-canonical-url (plist-get info :output-file)))
           (tags (concat
                  "<link rel=\"canonical\" href=\""
                  (ljos-html-escape-attr canon) "\">\n"
                  "<meta property=\"og:title\" content=\""
                  (ljos-html-escape-attr title) "\">\n"))
           (done nil))
      (replace-regexp-in-string
       "</head>"
       (lambda (match)
         (if done match
           (setq done t)
           (concat tags match)))
       output t t))))

(add-to-list 'org-export-filter-final-output-functions #'ljos-inject-canonical)

(setq org-publish-project-alist
      `(("handbook-org"
         :base-directory ,(expand-file-name "orgmode/handbook" default-directory)
         :base-extension "org"
         :publishing-directory ,(expand-file-name "handbook" default-directory)
         :publishing-function org-html-publish-to-html
         :recursive nil
         :headline-levels 4
         :with-toc nil
         :section-numbers nil
         :with-author nil
         :html-head-include-default-style nil
         :html-head-include-scripts nil)
        ("ljos-site" :components ("handbook-org"))))

;; A cache left by an earlier build can reuse a generated heading id, so
;; two builds of an unchanged file would not match. Publish from empty.
(setq org-publish-timestamp-directory
      (file-name-as-directory
       (expand-file-name "ljos-org-publish" temporary-file-directory)))
(let ((cache (expand-file-name "handbook-org.cache" org-publish-timestamp-directory)))
  (when (file-exists-p cache)
    (delete-file cache)))
(setq org-publish-cache nil)
(org-publish "ljos-site" t)

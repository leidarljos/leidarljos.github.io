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
      org-confirm-babel-evaluate nil)

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

(defun ljos-read-template (name)
  (let ((path (expand-file-name name
                                (expand-file-name "org/templates"
                                                  default-directory))))
    (with-temp-buffer
      (insert-file-contents path)
      (buffer-string))))

(setq org-html-head
      (concat "<style>\n" (engrave-faces-html-gen-stylesheet) "\n</style>\n"
              (ljos-read-template "head.html"))
      org-html-preamble (ljos-read-template "nav.html")
      org-html-postamble (ljos-read-template "footer.html"))

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
        ("docs-start-org"
         :base-directory ,(expand-file-name "orgmode/docs/start" default-directory)
         :base-extension "org"
         :publishing-directory ,(expand-file-name "docs/start" default-directory)
         :publishing-function org-html-publish-to-html
         :recursive nil
         :headline-levels 4
         :with-toc nil
         :section-numbers nil
         :with-author nil
         :html-head-include-default-style nil
         :html-head-include-scripts nil)
        ("ljos-site" :components ("handbook-org" "docs-start-org"))))

(org-publish "ljos-site" t)

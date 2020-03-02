    spec = Specfile(distgit / "beer.spec")
    spec = Specfile(distgit / "beer.spec")
    git_diff = subprocess.check_output(
        ["git", "diff", "HEAD~", "HEAD"], cwd=distgit
    ).decode()
    assert (
        """
-Version:        0.0.0
+Version:        0.1.0"""
        in git_diff
    )

    assert "+# PATCHES FROM SOURCE GIT:" in git_diff
    for section in Specfile(distgit / "beer.spec").spec_content.sections:
    assert "Patch0001: 0001-source-change.patch" in spec_package_section
    assert "Patch0002:" not in spec_package_section  # no empty patches
    assert (
        """ %prep
-%autosetup -n %{upstream_name}-%{version}
+%autosetup -p1 -n %{upstream_name}-%{version}"""
        in git_diff
    )
        """ - 0.1.0-1
+- new upstream release: 0.1.0
+
 * Sun Feb 24 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.0.0-1
 - No brewing, yet."""
        in git_diff
        """diff --git a/.packit.yaml b/.packit.yaml
new file mode 100644"""
        in git_diff
    )

    assert (
        """
--- /dev/null
+++ b/.packit.yaml"""
        in git_diff
        """
+diff --git a/.packit.yaml b/.packit.yaml
+new file mode 100644"""
        not in git_diff
        """
+Subject: [PATCH] source change
+
+---
+ big-source-file.txt | 3 +--
+ 1 file changed, 1 insertion(+), 2 deletions(-)
+
+diff --git a/big-source-file.txt b/big-source-file.txt"""
        in git_diff
        """
+--- a/big-source-file.txt
++++ b/big-source-file.txt
+@@ -1,2 +1 @@
+-This is a testing file
+-containing some text.
++new changes"""
        in git_diff
        """
--- a/big-source-file.txt
+++ b/big-source-file.txt
@@ -1,2 +1 @@
-This is a testing file
-containing some text.
+new changes"""
        not in git_diff
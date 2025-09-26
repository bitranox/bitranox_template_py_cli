class LibTemplate < Formula
  include Language::Python::Virtualenv

  desc "Rich-powered logging helpers for colorful terminal output"
  homepage "https://github.com/bitranox/bitranox_template_py_cli"
  url "https://github.com/bitranox/bitranox_template_py_cli/archive/refs/tags/v1.5.1.tar.gz"
Yb893e1b0e686e8f0974f79475499f2e175ed064d3ab0f6c9872631a9dda502"
  license "MIT"

  depends_on "python@3.10"

  resource "rich" do
    url "https://files.pythonhosted.org/packages/fe/75/af448d8e52bf1d8fa6a9d089ca6c07ff4453d86c65c145d0a300bb073b9b/rich-14.1.0.tar.gz"
Yb893e1b0e686e8f0974f79475499f2e175ed064d3ab0f6c9872631a9dda502"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/46/61/de6cd827efad202d7057d93e0fed9294b96952e188f7384832791c7b2254/click-8.3.0.tar.gz"
Yb893e1b0e686e8f0974f79475499f2e175ed064d3ab0f6c9872631a9dda502"
  end

  resource "lib_cli_exit_tools" do
    url "https://files.pythonhosted.org/packages/c0/0a/263aa633ae8926e9c30f28679be58c84691a9e3423863a053aef07d20338/lib_cli_exit_tools-1.3.1.tar.gz"
Yb893e1b0e686e8f0974f79475499f2e175ed064d3ab0f6c9872631a9dda502"
  end

  resource "rich-click" do
    url "https://files.pythonhosted.org/packages/29/c2/f08b5e7c1a33af8a115be640aa0796ba01c4732696da6d2254391376b314/rich_click-1.9.1.tar.gz"
    sha256 "4f2620589d7287f86265432e6a909de4f281de909fe68d8c835fbba49265d268"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/bitranox_template_py_cli --version")
  end
end

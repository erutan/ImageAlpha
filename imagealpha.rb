cask "imagealpha" do
  version "2.0.0"
  sha256 "CHECKSUM_HERE"

  url "https://github.com/erutan/ImageAlpha/releases/download/v#{version}/ImageAlpha-#{version}.zip"
  name "ImageAlpha"
  desc "PNG image optimization tool for reducing file sizes"
  homepage "https://github.com/erutan/ImageAlpha"

  livecheck do
    url :url
    strategy :github_latest
  end

  app "ImageAlpha.app"

  zap trash: [
    "~/Library/Preferences/net.pornel.ImageAlpha.plist",
    "~/Library/Saved Application State/net.pornel.ImageAlpha.savedState",
  ]
end

// Rasterize the original vector examples locally. No network access.
import AppKit
import CoreText
import Foundation

let args = CommandLine.arguments
guard args.count == 5 else {
    fatalError("Usage: render.swift INPUT.svg OUTPUT.png FONT_SANS.ttf FONT_SERIF.ttf")
}
for font in args[3...4] {
    let url = URL(fileURLWithPath: font) as CFURL
    CTFontManagerRegisterFontsForURL(url, .process, nil)
}
guard let image = NSImage(contentsOfFile: args[1]),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil),
      let png = NSBitmapImageRep(cgImage: cgImage).representation(using: .png, properties: [:]) else {
    fatalError("Unable to rasterize SVG")
}
try png.write(to: URL(fileURLWithPath: args[2]), options: .atomic)

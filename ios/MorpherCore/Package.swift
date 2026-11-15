// swift-tools-version: 5.7
import PackageDescription

let package = Package(
    name: "MorpherCore",
    platforms: [
        .iOS(.v16),
        .macOS(.v13),
    ],
    products: [
        .library(name: "MorpherCore", targets: ["MorpherCore"]),
    ],
    targets: [
        .target(name: "MorpherCore"),
        .testTarget(
            name: "MorpherCoreTests",
            dependencies: ["MorpherCore"],
            resources: [.copy("Fixtures")]
        ),
    ]
)

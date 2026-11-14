// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "MorpherCore",
    platforms: [
        .macOS(.v13),
        .iOS(.v16),
    ],
    products: [
        .library(name: "MorpherCore", targets: ["MorpherCore"]),
    ],
    targets: [
        .target(name: "MorpherCore", path: "Sources/MorpherCore"),
        .executableTarget(name: "morpher-demo", dependencies: ["MorpherCore"], path: "Sources/morpher-demo"),
        .testTarget(name: "MorpherCoreTests", dependencies: ["MorpherCore"], path: "Tests/MorpherCoreTests"),
    ],
    swiftLanguageVersions: [.v5]
)

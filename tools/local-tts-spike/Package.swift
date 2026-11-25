// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LocalTTSSpike",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "LocalTTSSpike", targets: ["LocalTTSSpike"])],
    dependencies: [
        .package(url: "https://github.com/k2-fsa/sherpa-onnx",
                 revision: "38016c6e0622e90bf417c35e8b47e0eb805af417"),
        .package(url: "https://github.com/csukuangfj/onnxruntime-libs", exact: "1.28.2")
    ],
    targets: [
        .target(name: "LocalTTSSpike", dependencies: [
            .product(name: "sherpa-onnx", package: "sherpa-onnx")
        ]),
        .target(name: "MobileOrtProbe", dependencies: [
            .product(name: "onnxruntime-ios", package: "onnxruntime-libs", condition: .when(platforms: [.iOS])),
            .product(name: "onnxruntime-macos", package: "onnxruntime-libs", condition: .when(platforms: [.macOS]))
        ], publicHeadersPath: "include", linkerSettings: [
            .linkedFramework("CoreML"), .linkedFramework("Foundation"),
            .linkedFramework("CoreFoundation"), .linkedLibrary("c++")
        ]),
        .testTarget(name: "LocalTTSSpikeTests", dependencies: ["LocalTTSSpike", "MobileOrtProbe"],
                    resources: [.copy("Resources")])
    ], cxxLanguageStandard: .cxx17
)

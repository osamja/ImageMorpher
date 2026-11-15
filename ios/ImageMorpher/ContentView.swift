import AVKit
import MorpherCore
import PhotosUI
import SwiftUI
import UIKit

struct ContentView: View {
    @StateObject private var viewModel = MorphViewModel()
    @State private var firstItem: PhotosPickerItem?
    @State private var secondItem: PhotosPickerItem?
    @State private var selectedHistory: MorphRecord?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    Text(
                        "Pick two faces. ImageMorpher crops them, finds "
                            + "landmarks, and morphs one into the other."
                    )
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)

                    HStack(spacing: 12) {
                        PhotoSlotView(
                            title: "First",
                            image: viewModel.firstPreview,
                            selection: $firstItem
                        )
                        PhotoSlotView(
                            title: "Second",
                            image: viewModel.secondPreview,
                            selection: $secondItem
                        )
                    }

                    controls

                    if let frame = viewModel.currentFrame {
                        Image(uiImage: frame)
                            .resizable()
                            .scaledToFit()
                            .clipShape(RoundedRectangle(cornerRadius: 18))
                    }

                    historySection
                }
                .padding()
            }
            .navigationTitle("Image Morpher")
        }
        .onChange(of: firstItem) { item in
            load(item, for: .first)
        }
        .onChange(of: secondItem) { item in
            load(item, for: .second)
        }
        .sheet(item: $selectedHistory) { record in
            NavigationStack {
                VStack(spacing: 16) {
                    VideoPlayer(
                        player: AVPlayer(
                            url: viewModel.videoURL(for: record)
                        )
                    )
                    .frame(maxHeight: .infinity)

                    Text(
                        record.createdAt.formatted(
                            date: .abbreviated,
                            time: .shortened
                        )
                    )
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                }
                .padding()
                .navigationTitle("Morph")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Done") { selectedHistory = nil }
                    }
                }
            }
        }
        .alert(
            "Something went wrong",
            isPresented: Binding(
                get: { viewModel.errorMessage != nil },
                set: { presented in
                    if !presented { viewModel.errorMessage = nil }
                }
            )
        ) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    @ViewBuilder
    private var controls: some View {
        switch viewModel.stage {
        case .processing(let completed, let total):
            VStack(spacing: 10) {
                ProgressView(
                    value: Double(completed),
                    total: Double(total)
                )
                Text("Generating frame \(completed) of \(total)")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                Button("Cancel", role: .destructive) {
                    viewModel.cancelMorph()
                }
            }
        case .loading:
            ProgressView("Preparing photos…")
        default:
            Button {
                viewModel.morph()
            } label: {
                Text(viewModel.canMorph ? "Morph" : "Choose two photos")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(!viewModel.canMorph)
        }

        if viewModel.frames.count > 1 {
            HStack(spacing: 16) {
                Button {
                    viewModel.isPlaying ? viewModel.pause() : viewModel.play()
                } label: {
                    Label(
                        viewModel.isPlaying ? "Pause" : "Play",
                        systemImage: viewModel.isPlaying ? "pause.fill" : "play.fill"
                    )
                }

                if let url = viewModel.videoURL {
                    ShareLink(item: url) {
                        Label("Share", systemImage: "square.and.arrow.up")
                    }
                }

                Button {
                    Task { await viewModel.saveToPhotos() }
                } label: {
                    Label(
                        viewModel.savedToPhotos ? "Saved" : "Save",
                        systemImage: viewModel.savedToPhotos
                            ? "checkmark.circle.fill"
                            : "square.and.arrow.down"
                    )
                }
                .disabled(
                    viewModel.videoURL == nil || viewModel.savedToPhotos
                )
            }
            .buttonStyle(.bordered)
        }
    }

    @ViewBuilder
    private var historySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("History")
                .font(.title3.bold())

            if viewModel.historyRecords.isEmpty {
                Text("Your morphs will appear here.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        ForEach(viewModel.historyRecords) { record in
                            Button {
                                selectedHistory = record
                            } label: {
                                VStack(alignment: .leading, spacing: 6) {
                                    if let thumbnail = viewModel.thumbnail(
                                        for: record
                                    ) {
                                        Image(uiImage: thumbnail)
                                            .resizable()
                                            .scaledToFill()
                                            .frame(width: 120, height: 120)
                                            .clipShape(
                                                RoundedRectangle(
                                                    cornerRadius: 12
                                                )
                                            )
                                    } else {
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(Color.secondary.opacity(0.2))
                                            .frame(width: 120, height: 120)
                                    }

                                    Text(
                                        record.createdAt.formatted(
                                            date: .abbreviated,
                                            time: .shortened
                                        )
                                    )
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                }
                            }
                            .buttonStyle(.plain)
                            .contextMenu {
                                Button(
                                    "Delete",
                                    role: .destructive
                                ) {
                                    viewModel.deleteHistory(record)
                                }
                            }
                        }
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func load(_ item: PhotosPickerItem?, for slot: MorphViewModel.Slot) {
        guard let item else { return }
        Task {
            guard let data = try? await item.loadTransferable(type: Data.self)
            else {
                return
            }
            await viewModel.setImageData(data, for: slot)
        }
    }
}

private struct PhotoSlotView: View {
    let title: String
    let image: UIImage?
    @Binding var selection: PhotosPickerItem?

    var body: some View {
        PhotosPicker(selection: $selection, matching: .images) {
            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.secondary.opacity(0.15))

                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                } else {
                    VStack(spacing: 8) {
                        Image(systemName: "person.crop.square")
                            .font(.largeTitle)
                        Text(title)
                            .font(.headline)
                    }
                    .foregroundStyle(.secondary)
                }
            }
            .frame(height: 180)
            .clipped()
        }
        .buttonStyle(.plain)
    }
}

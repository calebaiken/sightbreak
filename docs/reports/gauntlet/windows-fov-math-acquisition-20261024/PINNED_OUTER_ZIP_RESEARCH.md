# Pinned upload-artifact single-file outer ZIP bound

Read-only public-source research. No archive construction, native/helper/API invocation, test, CI or upload ran. All network/source-reader commands used CPU4. Only this own research report is written, outside existing branches.

## Result and assumptions

For exactly one immutable regular inner ZIP file of N bytes, with a short fixed ASCII outer member name of L bytes, explicit compression-level 0, the pinned upload-artifact client generates an outer ZIP of N + 114 + 2L bytes on the regular-file streaming path. This is a STORE payload bound, not an estimate of compression ratio.

| Component | Bytes |
|---|---:|
| Local file header and name | 30 + L |
| Unchanged stored payload | N |
| Signed non-ZIP64 data descriptor | 16 |
| Central file header and name | 46 + L |
| End of central directory | 22 |
| Total | N + 114 + 2L |

For N <= 16*1024*1024 and an explicitly frozen L <= 255, the resulting outer client ZIP is <= 16,777,840 bytes, below 32 MiB. The action does not enforce L <= 255; the workflow must supply the intended fixed path/name and exactly one regular file. N must bound bytes actually read, not merely an earlier stat of a subsequently growing file. No extra directory entries, comments, symlink substitution or forceZip64 option is included in this claim. Inner ZIP64 records remain opaque payload bytes and do not force ZIP64 on the outer archive.

This bounds the client-generated ZIP stream. It is not a measurement of a future uploaded/downloaded artifact, HTTP headers or an additional service/connector rewrapping layer.

## Pinned executable source and dependency identity

The action entry is action.yml:67-69, using node20 and dist/upload/index.js. The authoritative deployed bundle is pinned by action commit ea165f8d65b6e75b540449e92b4886f43607fa02, not a guessed toolkit source tag.

package-lock.json:36-39 pins @actions/artifact 2.3.2; 2530-2533 pins archiver 7.0.1; 7754-7760 pins zip-stream 6.0.1; 3107-3113 pins compress-commons 6.0.2; 3202-3208 pins crc32-stream 6.0.0. All metadata below refers to that pinned action bundle.

## Source derivation

- src/upload/input-helper.ts:43-51 parses the nonempty input string '0' into numeric zero and accepts range 0-9. src/upload/upload-artifact.ts:69-71 preserves numeric zero using an undefined check. Bundle line 3552 forwards options.compressionLevel to createZipUploadStream.
- Bundle 3768-3790 creates archiver('zip') with zlib.level=compressionLevel and appends each selected regular file with only its destination name. No forceZip64, comments or custom extras are passed. 3674-3699 distinguishes regular file entries from separately selected directories; the single-file assumption matters.
- Bundle 125233-125235 explicitly sets store=true when level===0 and !forceZip64. Actual zip-stream 6.0.1/index.js:41-43 agrees. Entry normalization defaults data.store from the archive option at 125253-125263; entry creation sets ZIP method 0 at 125325-125334. Archiver normalization does not inject a false store flag (57705-57714).
- Regular filesystem input becomes a stream at 57910-57912. _appendStream enables the data descriptor at 69577-69588. _smartStream selects CRC32Stream for STORE at 69652-69662. CRC32Stream 70247-70276 counts and forwards chunks unchanged, so compressed size equals N.
- Entry extra/comment fields begin null (69095-69107); getExtra returns the empty buffer (69166-69167), and both local/central extra getters return it (69121-69122,69202-69203). Timestamps use DOS fields, not automatic extended timestamp extras (69420-69425).
- ZIP64 entry size triggers require size or compressed size > 0xffffffff (69478-69479). Archive triggers are forceZip64, entry count > 0xffff, or central length/offset > 0xffffffff (69918-69919). None applies to one <=16 MiB file with the stated short name and default forceZip64=false (69604).
- Local header fields and name: 69856-69911, totaling 30+L with no extra. Stream data descriptor: 69839-69853, four 4-byte fields, totaling 16. Central header fields and name: 69750-69836, totaling 46+L with no extra/comment. EOCD: 69676-69706, totaling 22 with empty archive comment initialized at 69519-69527.
- ZipUploadStream is a byte-preserving Transform at 3756-3764; it adds no wrapper bytes to the produced ZIP stream.

All bundle line links can use:
https://github.com/actions/upload-artifact/blob/ea165f8d65b6e75b540449e92b4886f43607fa02/dist/upload/index.js#L3768-L3790

## Fetch failures retained

- https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/dist/index.js returned HTTP 404. action.yml identifies the correct dist/upload/index.js path.
- https://raw.githubusercontent.com/archiverjs/node-zip-stream/v6.0.1/index.js returned HTTP 404. The release source exists at tag 6.0.1 without the v prefix.
- Parent's earlier toolkit @actions/artifact@2.3.2 raw-tag 404 remains unresolved and was not used as evidence. The pinned deployed bundle closes the relevant source path.

## Exact fetched identities

| Source | URL | SHA-256 |
|---|---|---|
| Action metadata | https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/action.yml | 29b21270ff44638a165ea12abb4481796770c629e513217af7b4df1aa3821177 |
| Deployed bundle | https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/dist/upload/index.js | 0165b8a75330f3228f2c7a234b4ff8a107b9139c2b519147f4c8e9fe99b262d8 |
| Package lock | https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/package-lock.json | fddf66cd1d48dde834ddf318b0b0d6107174bc82298aef3e1f8e6e34b1adfe31 |
| Input parsing | https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/src/upload/input-helper.ts | 967817045a70ef97130acc41e0c99b1c78becfcca636ba22ddced1cb418a5867 |
| Option forwarding | https://raw.githubusercontent.com/actions/upload-artifact/ea165f8d65b6e75b540449e92b4886f43607fa02/src/upload/upload-artifact.ts | 3a8ccc15a820b4db83458cce1aa54de50702eb36c0e1f134d2a4718a089132ae |
| Archiver ZIP plugin | https://raw.githubusercontent.com/archiverjs/node-archiver/7.0.1/lib/plugins/zip.js | 3bbf3d7ae284820ab28ff2ae105f75fa4436f4edb2778f664abb7b56ad4a7090 |
| zip-stream release source | https://raw.githubusercontent.com/archiverjs/node-zip-stream/6.0.1/index.js | 29ea55ff9cf0007853d4ac51936278547299a601a00980bb373c002f21a85186 |

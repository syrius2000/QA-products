# Agent／Run EvidenceのSource Manifest

このディレクトリは、複数AIの元Evidenceを混在させずに再現するための固定参照領域である。

- `source-manifest.json`に、元Evidenceの保存場所、Agent／Run識別子、各ファイルのサイズとSHA-256を記録する。
- 元Evidenceの実体はアーカイブ済みChange側に保持し、現Changeへコピー・改変・再解釈しない。
- `agent_source_manifest.py --verify`で参照先の存在とハッシュを検証してから、`agent_aggregator.py --source-manifest`で再集計する。
- Token、Latency、正答率など取得不能な値は、Source ManifestによってObservedへ変換されない。

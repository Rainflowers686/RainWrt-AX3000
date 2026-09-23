# CR8808 board data

## Distribution status

RainWrt does not redistribute the two CR8808-specific ath11k board-data
containers below. Their byte-level provenance is traceable, but no explicit
vendor-origin permission covering these exact files has been established.
Their appearance in downstream repositories or possession in a device/firmware
image is not treated as a redistribution grant. Do not publish firmware images
that embed them.

| Local input | Radio | Tested board ID | Required SHA256 |
|---|---|---:|---|
| `board-redmi_ax3000.ipq5018` | IPQ5018 / 2.4 GHz | `0x10` | `a1d03029566e469ceee4d570324dfa015f3d01e351bc87c81329ffdd7a7c4186` |
| `board-redmi_ax3000.qcn6122` | QCN6122 / 5 GHz | `0x60` | `91c689226aa5a3af853063452393055c5e764866fec707ccd504738314e75134` |

These hashes identify the inputs used for the hardware-tested CR8808 build;
they do not assert ownership or grant rights. They are recorded so a builder
can verify that their own inputs match the tested bytes.

## Local preparation

Place exactly those two files, obtained and held under terms that permit your
local use, in the ignored directory:

```text
vendor-local/board-data/
├── board-redmi_ax3000.ipq5018
└── board-redmi_ax3000.qcn6122
```

RainWrt does not provide an unlicensed download link or a fragile stock-image
extractor. The files must be prepared locally by the person building the
firmware. The scripts do not connect to a router, download board data, or write
flash.

Run the verifier directly:

```sh
python3 scripts/local_bdf.py check
```

The build wrapper runs the same check before feed/network operations. Missing,
unexpected, symlinked, or hash-mismatched inputs fail closed. During the
`ipq-wifi` package prepare step, verified copies are injected only into the
ignored `build_dir` package staging directory; they are not copied back into
tracked source. The local input directory is ignored by Git and the public
source audit confirms the ignore rules and Git-object history.

## Scope and limitations

- Only the CR8808 / `redmi_ax3000` M81 build path has this local-input helper.
- The Xiaomi CR880X M79 reference pair is also excluded from public source
  history; M79 is not authorized or validated for sysupgrade and is not a
  supported binary build target in this public-source workflow.
- A build made with local inputs is not automatically approved for publication.
  Firmware binary distribution remains blocked until redistribution rights are
  established for every embedded board-data and firmware component.
- The public source representation is sanitized and is not byte-for-byte the
  original hardware-tested Git tree. See
  [hardware validation](HARDWARE_VALIDATION.md) and
  [the public release audit](PUBLIC_RELEASE_AUDIT.md).

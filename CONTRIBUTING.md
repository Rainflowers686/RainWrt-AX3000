# Contributing to RainWrt

RainWrt follows ImmortalWrt stable and keeps device-specific changes reviewable. Explain the target device, upstream baseline and reason for a downstream patch.

## Source checks

The [source-audit workflow](.github/workflows/build.yml) records the checks used by the project. Before submitting changes that affect upgrade handling, run the relevant checks from a Linux environment and include their output summary:

```sh
python3 tests/test_hardware_runner.py
sh tests/mi_layout_test.sh
sh tests/mi_dualboot_test.sh
git diff --check
```

Use the workflow for the complete source/privacy test list. These source tests do not establish compatibility with a router that has not been tested.

## Hardware claims and builds

Record the exact model, board revision, bootloader, flash layout, build identity and checks performed. Read [UPGRADE_SAFETY.md](docs/UPGRADE_SAFETY.md) and [RECOVERY.md](docs/RECOVERY.md) before any device operation. Keep unknown layouts unsupported until there is evidence for them.

Local board-data inputs are described in [BOARD_DATA.md](docs/BOARD_DATA.md). Do not attach them, private configurations or firmware images containing uncleared components to a pull request. Retain upstream licenses, copyright notices and package-level terms.

For documentation changes, update both README language versions and preserve the distinction between build, source test, hardware test and recovery validation.

## 中文说明

请说明补丁对应的设备、上游基线和保留下游改动的原因。源码测试、构建成功、硬件验证和恢复验证分别记录；没有实测的设备不要写成兼容。不要提交本地 board-data、私人配置或包含未获再分发许可组件的固件，保留上游和各包原有的许可声明。

# History Split

This repository was separated from the former mixed PCOT/plugin repository on 2026-06-10.

The full original Git history was retained, including PCOT file diffs. The current tree was then cleaned in a final commit so that the repository now contains only the distance estimation plugin, its data, and its plugin-specific tests.

Original mixed repository remote:

```text
https://github.com/henryh0we/Calculating-Distance-Plugin-for-PCOT.git
```

PCOT compatibility baseline:

```text
42fc68b898904b273d40061590d9c534e7df2587
```

That commit is the PCOT release base where the distance estimation plugin work started:

```text
42fc68b VERSION BUMP (and readme edit) for release 0.9.0-alpha 2025-02-17 GODOLPHIN HILL
```

Unlike a filtered split, this repository intentionally keeps the original historical commits and their original hashes up to the cleanup commit. The cleanup commit removes PCOT from the current working tree and moves the plugin to the repository root.

#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

python3 -m pip install -e ".[build]"
python3 -m PyInstaller --noconfirm --clean --onedir --name "virt-pet" virtpet/main.py

release_dir="$project_root/dist/virt-pet"
for asset_dir in runtime models THIRD_PARTY_LICENSES; do
    if [[ -d "$project_root/$asset_dir" ]]; then
        cp -R "$project_root/$asset_dir" "$release_dir/"
    fi
done
cp "$project_root/README.md" "$project_root/LICENSE" "$release_dir/"

archive="$project_root/dist/virt-pet-linux-x64.tar.gz"
rm -f "$archive"
tar -C "$release_dir" -czf "$archive" .
echo "Built $archive"

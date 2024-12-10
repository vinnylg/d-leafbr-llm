#!/bin/bash

function print_tree {
    local dir="$1"
    local prefix="$2"
    local is_last="$3"

    # Lista apenas arquivos e diretórios não ocultos (exclui PDFs)
    local entries=($(find "$dir" -mindepth 1 -maxdepth 1 ! -iname ".*" ! -iname "*.pdf" ! -iname "tree.sh" | sort))
    local count=${#entries[@]}
    local index=1

    for entry in "${entries[@]}"; do
        local base=$(basename "$entry")
        local connector="├──"
        local new_prefix="$prefix│   "

        if [ "$index" -eq "$count" ]; then
            connector="└──"
            new_prefix="$prefix    "
        fi

        echo "${prefix}${connector} ${base}"

        if [ -d "$entry" ]; then
            print_tree "$entry" "$new_prefix"
        fi

        index=$((index + 1))
    done
}

# Diretório inicial (padrão é o atual)
root_dir=${1:-.}
echo "$root_dir"
print_tree "$root_dir" ""


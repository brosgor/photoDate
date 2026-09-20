#!/usr/bin/env python3
"""photoDate — GUI de escritorio + CLI. Multiplataforma (Windows / macOS / Linux)."""

from __future__ import annotations

import argparse
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from stamp import IMAGE_EXTS, process_files, process_folder, resolve_when, stamp

FILETYPES = [
    ("Imágenes", " ".join(f"*{e}" for e in sorted(IMAGE_EXTS))),
    ("Todos", "*.*"),
]


def run_gui() -> None:
    root = tk.Tk()
    root.title("photoDate")
    root.minsize(520, 340)
    root.geometry("580x360")

    mode_var = tk.StringVar(value="carpeta")  # carpeta | archivos
    path_var = tk.StringVar()
    selected_files: list[Path] = []
    force_var = tk.BooleanVar(value=False)
    time_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
    status_var = tk.StringVar(
        value="Por defecto cada foto usa su propia fecha/hora (metadata EXIF)."
    )
    progress = tk.DoubleVar(value=0)

    frm = ttk.Frame(root, padding=16)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frm, text="Modo").grid(row=0, column=0, sticky="w")
    mode_row = ttk.Frame(frm)
    mode_row.grid(row=1, column=0, sticky="w", pady=(4, 8))
    ttk.Radiobutton(
        mode_row, text="Carpeta (lote)", variable=mode_var, value="carpeta"
    ).pack(side=tk.LEFT, padx=(0, 16))
    ttk.Radiobutton(
        mode_row,
        text="Archivo(s) (individual / varios)",
        variable=mode_var,
        value="archivos",
    ).pack(side=tk.LEFT)

    path_label = ttk.Label(frm, text="Carpeta de fotos")
    path_label.grid(row=2, column=0, sticky="w")
    path_row = ttk.Frame(frm)
    path_row.grid(row=3, column=0, sticky="ew", pady=(4, 8))
    path_row.columnconfigure(0, weight=1)
    ttk.Entry(path_row, textvariable=path_var).grid(row=0, column=0, sticky="ew")

    def browse() -> None:
        selected_files.clear()
        if mode_var.get() == "carpeta":
            chosen = filedialog.askdirectory(title="Seleccionar carpeta")
            if chosen:
                path_var.set(chosen)
        else:
            chosen = filedialog.askopenfilenames(
                title="Seleccionar foto(s)",
                filetypes=FILETYPES,
            )
            if chosen:
                selected_files.extend(Path(p) for p in chosen)
                if len(selected_files) == 1:
                    path_var.set(str(selected_files[0]))
                else:
                    path_var.set(f"{len(selected_files)} archivos seleccionados")

    ttk.Button(path_row, text="Examinar…", command=browse).grid(
        row=0, column=1, padx=(8, 0)
    )

    def on_mode_change(*_args) -> None:
        selected_files.clear()
        path_var.set("")
        if mode_var.get() == "carpeta":
            path_label.configure(text="Carpeta de fotos")
            status_var.set(
                "Lote: cada foto de la carpeta con su propia fecha EXIF."
            )
        else:
            path_label.configure(text="Foto(s)")
            status_var.set(
                "Elige una o varias fotos; cada una con su propia fecha EXIF."
            )

    mode_var.trace_add("write", on_mode_change)

    ttk.Label(
        frm,
        text="Por defecto: cada foto usa su fecha/hora de metadata (EXIF).",
    ).grid(row=4, column=0, sticky="w", pady=(4, 0))

    force_cb = ttk.Checkbutton(
        frm,
        text="Opcional: usar fecha/hora personalizada en todas",
        variable=force_var,
    )
    force_cb.grid(row=5, column=0, sticky="w", pady=(8, 0))

    time_row = ttk.Frame(frm)
    time_row.grid(row=6, column=0, sticky="ew", pady=(4, 12))
    time_row.columnconfigure(1, weight=1)
    ttk.Label(time_row, text="YYYY-MM-DD HH:MM").grid(row=0, column=0, sticky="w")
    time_entry = ttk.Entry(time_row, textvariable=time_var, state=tk.DISABLED)
    time_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def on_force_toggle(*_args) -> None:
        time_entry.configure(state=tk.NORMAL if force_var.get() else tk.DISABLED)

    force_var.trace_add("write", on_force_toggle)

    bar = ttk.Progressbar(frm, variable=progress, maximum=100)
    bar.grid(row=7, column=0, sticky="ew", pady=(0, 8))
    ttk.Label(frm, textvariable=status_var, wraplength=520).grid(
        row=8, column=0, sticky="w"
    )

    btn = ttk.Button(frm, text="Procesar → *_fechada")
    btn.grid(row=9, column=0, sticky="ew", pady=(16, 0))
    frm.columnconfigure(0, weight=1)

    def set_busy(busy: bool) -> None:
        btn.configure(state=tk.DISABLED if busy else tk.NORMAL)

    def parse_forced() -> datetime | None:
        if not force_var.get():
            return None
        return datetime.strptime(time_var.get().strip(), "%Y-%m-%d %H:%M")

    def on_progress(i: int, total: int, name: str) -> None:
        def update(i=i, total=total, name=name) -> None:
            progress.set(100 * i / total)
            status_var.set(f"{i}/{total}: {name}")

        root.after(0, update)

    def worker(job, forced: datetime | None) -> None:
        try:
            if isinstance(job, list):
                out = process_files(job, forced=forced, on_progress=on_progress)
            else:
                out = process_folder(job, forced=forced, on_progress=on_progress)
        except Exception as exc:  # noqa: BLE001 — mostrar en UI
            err = str(exc)

            def fail(msg=err) -> None:
                set_busy(False)
                status_var.set("Error.")
                messagebox.showerror("photoDate", msg)

            root.after(0, fail)
            return

        def done(path=out) -> None:
            set_busy(False)
            progress.set(100)
            status_var.set(f"Listo: {path}")
            messagebox.showinfo("photoDate", f"Fotos guardadas en:\n{path}")

        root.after(0, done)

    def start() -> None:
        try:
            forced = parse_forced()
        except ValueError:
            messagebox.showerror(
                "photoDate",
                "Fecha inválida. Usa el formato YYYY-MM-DD HH:MM",
            )
            return

        if mode_var.get() == "carpeta":
            raw = path_var.get().strip()
            if not raw:
                messagebox.showwarning("photoDate", "Elige una carpeta.")
                return
            folder = Path(raw)
            if not folder.is_dir():
                messagebox.showerror("photoDate", f"No es una carpeta:\n{folder}")
                return
            job: Path | list[Path] = folder
        else:
            files = list(selected_files)
            if not files and path_var.get().strip():
                # ruta pegada a mano
                p = Path(path_var.get().strip())
                if p.is_file():
                    files = [p]
            if not files:
                messagebox.showwarning("photoDate", "Elige una o más fotos.")
                return
            job = files

        set_busy(True)
        progress.set(0)
        status_var.set("Procesando…")
        threading.Thread(target=worker, args=(job, forced), daemon=True).start()

    btn.configure(command=start)
    root.mainloop()


def run_cli(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Marca de agua de fecha/hora. Sin args abre la interfaz."
    )
    p.add_argument(
        "ruta",
        nargs="?",
        type=Path,
        help="carpeta (lote) o archivo (→ *_fechada)",
    )
    p.add_argument("-o", "--output", type=Path, help="salida (solo un archivo)")
    p.add_argument(
        "-t",
        "--time",
        help="forzar la misma fecha/hora en todas: YYYY-MM-DD HH:MM",
    )
    args = p.parse_args(argv)

    if args.ruta is None:
        run_gui()
        return 0

    forced = (
        datetime.strptime(args.time, "%Y-%m-%d %H:%M") if args.time else None
    )
    src = args.ruta.expanduser().resolve()

    if src.is_dir():
        print(process_folder(src, forced=forced))
        return 0

    if not src.is_file():
        print(f"No existe: {src}", file=sys.stderr)
        return 1

    if args.output:
        when = resolve_when(src, forced)
        dst = args.output.expanduser().resolve()
        stamp(src, dst, when)
        print(dst)
    else:
        print(process_files([src], forced=forced))
    return 0


def main() -> int:
    return run_cli()


if __name__ == "__main__":
    raise SystemExit(main())

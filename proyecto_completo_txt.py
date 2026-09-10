import os

# -----------------------------------
# CONFIG
# -----------------------------------
CARPETA_PROYECTO = r"./"

ARCHIVO_SALIDA = "proyecto_completo.txt"

EXTENSIONES = [".py"]

# Archivos a excluir
EXCLUIR = [
    "proyecto_completo_txt.py"
]

# -----------------------------------
# GENERAR TXT
# -----------------------------------
with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as salida:

    for root, dirs, files in os.walk(CARPETA_PROYECTO):

        # Ignorar carpetas innecesarias
        dirs[:] = [
            d for d in dirs
            if d not in [
                "__pycache__",
                ".git",
                ".venv",
                "venv"
            ]
        ]

        for archivo in sorted(files):

            # Excluir archivos específicos
            if archivo in EXCLUIR:
                continue

            if any(
                archivo.endswith(ext)
                for ext in EXTENSIONES
            ):

                ruta_archivo = os.path.join(
                    root,
                    archivo
                )

                try:

                    with open(
                        ruta_archivo,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        contenido = f.read()

                    salida.write(
                        "\n"
                        + "=" * 80
                        + "\n"
                    )

                    salida.write(
                        f"ARCHIVO: {ruta_archivo}\n"
                    )

                    salida.write(
                        "=" * 80
                        + "\n\n"
                    )

                    salida.write(contenido)

                    salida.write("\n\n")

                    print(
                        f"[OK] {ruta_archivo}"
                    )

                except Exception as e:

                    print(
                        f"[ERROR] {ruta_archivo} -> {e}"
                    )

print(
    f"\nArchivo generado: {ARCHIVO_SALIDA}"
)

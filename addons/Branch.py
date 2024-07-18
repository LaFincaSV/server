import subprocess
import os
import shutil
import sys
import time
import json

def run_command(command):
    """Ejecutar un comando en el sistema y verificar si fue exitoso."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"[+] Error: {e}\n{e.stderr}"
        print(gradient_text(error_message, [(255, 0, 0), (255, 128, 0)]))
        input(gradient_text("Presiona cualquier tecla para continuar...", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(color1, color2, t):
    r = int(lerp(color1[0], color2[0], t))
    g = int(lerp(color1[1], color2[1], t))
    b = int(lerp(color1[2], color2[2], t))
    return (r, g, b)

def rgb_to_ansi(r, g, b):
    return f'\033[38;2;{r};{g};{b}m'

def gradient_text(text, colors):
    length = len(text)
    num_colors = len(colors)
    result = ""
    for i, char in enumerate(text):
        color_index = (i * (num_colors - 1)) // length
        t = (i * (num_colors - 1)) / length - color_index
        color1 = colors[color_index]
        color2 = colors[color_index + 1] if color_index + 1 < num_colors else colors[color_index]
        color = lerp_color(color1, color2, t)
        result += rgb_to_ansi(*color) + char
    return result + '\033[0m'

def copy_files(source_dir, target_dir, retries=3, delay=1):
    """Copiar todos los archivos y carpetas de source_dir a target_dir."""
    for item in os.listdir(source_dir):
        source_path = os.path.join(source_dir, item)
        target_path = os.path.join(target_dir, item)
        if os.path.isdir(source_path):
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)
        else:
            for attempt in range(retries):
                try:
                    shutil.copy2(source_path, target_path)
                    break
                except OSError as e:
                    if e.errno == 26:  # Text file busy
                        time.sleep(delay)
                    else:
                        raise

def create_temp_json(repo_url):
    """Crear un archivo JSON temporal con la URL del repositorio."""
    temp_data = {"repo_url": repo_url}
    temp_file = "temp_repo_url.json"
    with open(temp_file, 'w') as f:
        json.dump(temp_data, f)
    return temp_file

def delete_temp_json(temp_file):
    """Eliminar el archivo JSON temporal."""
    if os.path.exists(temp_file):
        os.remove(temp_file)

def branch():
    new_branch_name = "Minecraft_branch"
    commit_message = "Branch para guardar tu server_minecraft"

    # Obtener información del repositorio
    repo_url = run_command(["git", "config", "--get", "remote.origin.url"])
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    username = repo_url.split('/')[-2]

    # Agregar solo la carpeta servidor_minecraft
    run_command(["git", "add", "--force", "."])

    # Verificar si hay cambios para hacer commit
    changes = run_command(["git", "status", "--porcelain"])
    if changes:
        run_command(["git", "commit", "-m", commit_message])

        # Crear y cambiar al nuevo branch
        run_command(["git", "checkout", "-B", new_branch_name])
        
        # Subir el nuevo branch al repositorio
        try:
            run_command(["git", "push", "-f", "origin", new_branch_name])
        except subprocess.CalledProcessError as e:
            print(gradient_text(f"[+] Error al subir el branch: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
            input(gradient_text("Presiona cualquier tecla para continuar...", [(255, 0, 0), (255, 128, 0)]))
            sys.exit(1)
        
        branch_url = f"https://github.com/{username}/{repo_name}/tree/{new_branch_name}"
        print(gradient_text(f"\nBranch creado/actualizado localmente: {new_branch_name}\nEnlace al branch (local): {branch_url}\n\nAcuerdate de copiar el enlace para tu nueva cuenta", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    else:
        print(gradient_text("[+] No hay cambios para confirmar.", [(255, 0, 0), (255, 128, 0)]))
    
    input(gradient_text("\nPresiona cualquier tecla para continuar...", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    sys.exit(0)

def link():
    prompt_text = gradient_text("Introduce el enlace del repositorio: ", [(0, 255, 0), (0, 128, 255), (255, 0, 255)])
    repo_url = input(prompt_text).strip()
    branch_name = "Minecraft_branch"
    
    # Crear archivo JSON temporal
    temp_file = create_temp_json(repo_url)

    # Leer el URL del archivo JSON temporal
    with open(temp_file, 'r') as f:
        temp_data = json.load(f)
    repo_url = temp_data["repo_url"]

    # Clonar el repositorio y el branch especificado
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    cloned_repo_dir = os.path.join(os.getcwd(), repo_name)
    run_command(["git", "clone", "--branch", branch_name, "--single-branch", repo_url, cloned_repo_dir])

    # Mover solo la carpeta servidor_minecraft del repositorio clonado al repositorio actual
    source_path = os.path.join(cloned_repo_dir, "servidor_minecraft")
    target_path = os.path.join(os.getcwd(), "servidor_minecraft")
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    shutil.move(source_path, target_path)

    # Borrar la carpeta clonada para evitar errores de autor
    if os.path.exists(cloned_repo_dir):
        shutil.rmtree(cloned_repo_dir)

    # Leer el URL original del remoto del archivo JSON temporal
    with open(temp_file, 'r') as f:
        temp_data = json.load(f)
    original_repo_url = temp_data["repo_url"]

    # Restablecer el URL del remoto al repositorio del usuario
    run_command(["git", "remote", "set-url", "origin", original_repo_url])

    # Eliminar el archivo JSON temporal
    delete_temp_json(temp_file)

    # Agregar la carpeta servidor_minecraft y hacer commit
    run_command(["git", "add", "--force", "servidor_minecraft"])
    run_command(["git", "commit", "-m", f"Add files from {repo_name}"])

    # Crear y cambiar al nuevo branch
    run_command(["git", "checkout", "-B", branch_name])

    # Subir el nuevo branch al repositorio
    try:
        run_command(["git", "push", "-u", "origin", branch_name])
    except subprocess.CalledProcessError as e:
        print(gradient_text(f"[+] Error al subir el branch: {e.stderr}", [(255, 0, 0), (255, 128, 0)]))
        input(gradient_text("Presiona cualquier tecla para continuar...", [(255, 0, 0), (255, 128, 0)]))
        sys.exit(1)

    print(gradient_text(f"\nBranch clonado y subido a tu propio repositorio exitosamente.", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    input(gradient_text("\nPresiona cualquier tecla para continuar...", [(0, 255, 0), (0, 128, 255), (255, 0, 255)]))
    sys.exit(0)
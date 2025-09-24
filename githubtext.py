import os
import subprocess
import shutil
import stat
import time
from pathlib import Path


github_user = "eoeoe22"


def generate_tree_structure(root_dir, exclude_dirs=None):
    """폴더 구조를 tree 형식으로 생성"""
    if exclude_dirs is None:
        exclude_dirs = set()
    
    tree_lines = []
    
    def add_tree_line(path, prefix="", is_last=True):
        if path.is_file():
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")
        else:
            if path != Path(root_dir):
                connector = "└── " if is_last else "├── "
                # 제외 폴더 특별 처리
                if path.name in exclude_dirs:
                    if path.name == '.git':
                        tree_lines.append(f"{prefix}{connector}{path.name}/ [Git 버전 관리 폴더]")
                    else:
                        tree_lines.append(f"{prefix}{connector}{path.name}/ [제외됨]")
                    return  # 하위 폴더 탐색 중단
                else:
                    tree_lines.append(f"{prefix}{connector}{path.name}/")
                
                extension = "    " if is_last else "│   "
                new_prefix = prefix + extension
            else:
                tree_lines.append(f"{path.name}/")
                new_prefix = ""
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                # 제외할 디렉토리 필터링
                items = [item for item in items if not (item.is_dir() and item.name in exclude_dirs)]
                
                # 100개 이상의 파일이 있는 폴더 처리
                if len(items) > 100:
                    # 파일 타입별로 개수 세기
                    file_counts = {}
                    dir_count = 0
                    
                    for item in items:
                        if item.is_file():
                            ext = item.suffix.lower()
                            if is_audio_file(item.name):
                                if ext in ['.mp3', '.wav']:
                                    file_counts[ext] = file_counts.get(ext, 0) + 1
                                else:
                                    file_counts['기타 오디오'] = file_counts.get('기타 오디오', 0) + 1
                            else:
                                file_counts[ext if ext else '확장자 없음'] = file_counts.get(ext if ext else '확장자 없음', 0) + 1
                        else:
                            dir_count += 1
                    
                    # 디렉토리 먼저 표시
                    dirs = [item for item in items if item.is_dir()]
                    for i, item in enumerate(dirs):
                        is_last_item = i == len(dirs) - 1 and len(file_counts) == 0
                        add_tree_line(item, new_prefix, is_last_item)
                    
                    # 파일 개수 요약 표시
                    file_summary = []
                    for ext, count in sorted(file_counts.items()):
                        if ext in ['.mp3', '.wav']:
                            file_summary.append(f"{count}개의 {ext[1:]} 파일")
                        elif ext == '기타 오디오':
                            file_summary.append(f"{count}개의 기타 오디오 파일")
                        else:
                            file_summary.append(f"{count}개의 {ext} 파일")
                    
                    if file_summary:
                        summary_text = ", ".join(file_summary)
                        connector = "└── "
                        tree_lines.append(f"{new_prefix}{connector}[{summary_text}]")
                else:
                    # 100개 미만인 경우 기존 방식대로 표시
                    for i, item in enumerate(items):
                        is_last_item = i == len(items) - 1
                        add_tree_line(item, new_prefix, is_last_item)
                        
            except PermissionError:
                pass
    
    add_tree_line(Path(root_dir))
    return "\n".join(tree_lines)

def is_audio_file(filename):
    """오디오 파일인지 확인"""
    audio_exts = {
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',
        '.m4a', '.aiff', '.au', '.ra', '.3gp', '.amr',
        '.m4r', '.opus', '.webm', '.mp4a', '.ac3',
        '.dts', '.ape', '.mka', '.mp2', '.m3u', '.m3u8',
        '.pls', '.cue', '.dsf', '.dff'
    }
    ext = os.path.splitext(filename)[1].lower()
    return ext in audio_exts

def collect_code_files(root_dir, exclude_dirs=None):
    """웹개발용 코드 파일들을 수집 (확장된 확장자 지원)"""
    if exclude_dirs is None:
        exclude_dirs = set()
    
    # 웹개발용 확장자 목록 (대폭 확장)
    include_exts = {
        # 기본 웹 기술
        '.html', '.htm', '.css', '.js', '.json',
        # 프론트엔드 프레임워크/라이브러리
        '.jsx', '.tsx', '.vue', '.svelte',
        # CSS 전처리기
        '.scss', '.sass', '.less', '.stylus',
        # 백엔드 언어
        '.php', '.py', '.java', '.rb', '.go', '.rs', '.kt',
        # 서버 스크립트
        '.ts', '.mjs', '.cjs',
        # 설정 파일
        '.toml', '.yaml', '.yml', '.ini', '.env',
        # 데이터베이스
        '.sql', '.sqlite', '.db',
        # 마크업/문서
        '.md', '.txt', '.xml', '.svg',
        # 빌드/패키지 관리
        '.dockerfile', '.dockerignore', '.gitignore',
        # 기타 웹 관련
        '.htaccess', '.nginx', '.conf'
    }
    
    file_contents = {}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 제외할 디렉토리들을 dirnames에서 제거
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            # 확장자가 없는 특정 파일들도 포함 (Dockerfile, Makefile 등)
            special_files = {'dockerfile', 'makefile', 'rakefile', 'gemfile', 'procfile'}
            
            # 오디오 파일이 아니고 포함할 확장자이거나 특별한 파일인 경우
            if not is_audio_file(filename) and (ext in include_exts or filename.lower() in special_files):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    rel_path = os.path.relpath(filepath, root_dir)
                    file_contents[rel_path] = content
                except UnicodeDecodeError:
                    # 바이너리 파일인 경우 건너뛰기
                    continue
                except Exception as e:
                    rel_path = os.path.relpath(filepath, root_dir)
                    file_contents[rel_path] = f'Error reading file: {e}'
    
    return file_contents

def clone_repository(repo_name):
    """GitHub 레포지토리를 클론"""
    clone_url = f"https://github.com/{github_user}/{repo_name}.git"
    print(f"레포지토리를 클론합니다: {clone_url}")
    
    try:
        # Windows cmd에서 git clone 실행
        result = subprocess.run(
            ["git", "clone", clone_url], 
            check=True, 
            capture_output=True, 
            text=True
        )
        print("✅ 클론 성공!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ git clone 실패: {e}")
        print(f"오류 출력: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Git이 설치되지 않았거나 PATH에 등록되지 않았습니다.")
        print("Git을 설치하거나 환경변수를 확인해주세요.")
        return False

def get_repository_input():
    """사용자로부터 레포지토리 이름 입력받기"""
    print("=" * 50)
    print("깃허브 래포지토리 텍스트추출기")
    print("=" * 50)
    
    while True:
        print(f"유저 : {github_user}\n분석할 GitHub 레포지토리 이름을 입력하세요:")

        
        repo_name = input("\n레포지토리 이름 입력: ").strip()
        
        if not repo_name:
            print("❌ 레포지토리 이름을 입력해야 합니다.")
            retry = input("다시 입력하시겠습니까? (y/n): ").strip().lower()
            if retry != 'y':
                return None
            continue
        
        # 유효한 레포지토리 이름인지 간단 검사
        if '/' in repo_name:
            print("❌ 레포지토리 이름에는 '/'를 포함할 수 없습니다.")
            print("예: 'my-project' (올바름), 'user/my-project' (잘못됨)")
            continue
        
        return repo_name

def get_output_filename():
    """출력 파일명 입력받기"""
    while True:
        print("\n분석 결과를 저장할 텍스트 파일명을 입력하세요:")
        print(" - Enter만 누르면 기본값 사용 (github_analysis.txt)")
        
        output_filename = input("\n파일명 입력: ").strip()
        
        # 빈 입력인 경우 기본값 사용
        if not output_filename:
            output_filename = "github_analysis.txt"
            print(f"기본 파일명을 사용합니다: {output_filename}")
            break
        
        # 파일명 유효성 검사
        invalid_chars = '<>:"/\\|?*'
        if any(char in output_filename for char in invalid_chars):
            print("❌ 파일명에 사용할 수 없는 문자가 포함되어 있습니다.")
            print(f"사용할 수 없는 문자: {invalid_chars}")
            continue
        
        # 확장자가 없으면 .txt 추가
        if not os.path.splitext(output_filename)[1]:
            output_filename += ".txt"
            print(f"확장자를 추가했습니다: {output_filename}")
        
        break
    
    return output_filename

def save_analysis_result(project_folder, output_filename):
    """분석 결과를 파일로 저장"""
    exclude_dirs = {'.git', 'node_modules', '__pycache__', '.vscode', '.idea'}
    
    print("📊 프로젝트 구조를 분석하는 중...")
    tree_structure = generate_tree_structure(project_folder, exclude_dirs)
    
    print("📁 코드 파일들을 수집하는 중...")
    file_contents = collect_code_files(project_folder, exclude_dirs)
    
    print("💾 결과를 저장하는 중...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("=== Workers 환경 프로젝트 구조 분석 ===\n\n")
        f.write("=== 폴더 구조 ===\n")
        f.write(tree_structure)
        f.write("\n\n")
        
        if exclude_dirs:
            f.write("=== 제외된 폴더 정보 ===\n")
            for folder in exclude_dirs:
                if folder == '.git':
                    f.write(".git/ - Git 버전 관리 폴더입니다.\n")
                elif folder == 'node_modules':
                    f.write("node_modules/ - Node.js 의존성 패키지 폴더입니다.\n")
                elif folder == '__pycache__':
                    f.write("__pycache__/ - Python 캐시 폴더입니다.\n")
                elif folder == '.vscode':
                    f.write(".vscode/ - Visual Studio Code 설정 폴더입니다.\n")
                elif folder == '.idea':
                    f.write(".idea/ - IntelliJ IDEA 설정 폴더입니다.\n")
            f.write("\n")
        
        f.write("=== 코드 파일 내용 ===\n\n")
        
        if not file_contents:
            f.write("지정된 확장자의 웹개발용 코드 파일을 찾을 수 없습니다.\n")
        else:
            for rel_path in sorted(file_contents.keys()):
                content = file_contents[rel_path]
                f.write(f"===== {rel_path} =====\n")
                f.write(content)
                f.write(f"\n" + "="*50 + "\n\n")
    
    print(f"✅ 분석 완료! 결과가 '{output_filename}' 파일에 저장되었습니다.")
    print(f"📊 처리된 코드 파일: {len(file_contents)}개")

def cleanup_folder(folder_path):
    """클론된 폴더를 안전하게 삭제 (Windows 읽기 전용 파일 처리)"""
    def handle_remove_readonly(func, path, exc):
        """읽기 전용 파일/폴더 삭제 처리"""
        try:
            # 읽기 전용 속성 제거
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            print(f"⚠️ 파일 삭제 실패: {path} - {e}")
    
    try:
        print(f"🗑️ 클론된 폴더를 삭제합니다: {folder_path}")
        
        # Windows에서 Git 폴더 삭제를 위한 강력한 방법
        if os.path.exists(folder_path):
            # 첫 번째 시도: 읽기 전용 속성 제거 후 삭제
            shutil.rmtree(folder_path, onerror=handle_remove_readonly)
            
            # 삭제 확인
            if os.path.exists(folder_path):
                print("⏳ 첫 번째 삭제 시도 실패, 다른 방법으로 재시도...")
                
                # 두 번째 시도: 모든 파일의 속성을 변경한 후 삭제
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, stat.S_IWRITE)
                        except:
                            pass
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.chmod(dir_path, stat.S_IWRITE)
                        except:
                            pass
                
                # 잠시 대기 후 재시도
                time.sleep(1)
                shutil.rmtree(folder_path, ignore_errors=True)
                
                # 최종 확인
                if os.path.exists(folder_path):
                    print("⏳ 두 번째 삭제 시도도 실패, Windows 명령어로 강제 삭제...")
                    
                    # 세 번째 시도: Windows rmdir 명령어 사용
                    try:
                        subprocess.run(
                            ["rmdir", "/s", "/q", folder_path], 
                            shell=True, 
                            check=True,
                            capture_output=True
                        )
                    except subprocess.CalledProcessError:
                        print("⚠️ Windows 명령어도 실패했습니다.")
        
        # 최종 삭제 확인
        if not os.path.exists(folder_path):
            print("✅ 폴더 삭제 완료!")
        else:
            print(f"⚠️ 폴더 삭제에 실패했습니다: {folder_path}")
            print("수동으로 삭제해주세요.")
            
    except Exception as e:
        print(f"❌ 폴더 삭제 중 오류 발생: {e}")
        print(f"수동으로 삭제해주세요: {folder_path}")

def main():
    """메인 함수"""
    project_folder = None
    try:
        # 1. 사용자로부터 레포지토리 이름 입력받기
        repo_name = get_repository_input()
        if not repo_name:
            print("프로그램을 종료합니다.")
            return
        
        # 2. GitHub 레포지토리 클론
        if not clone_repository(repo_name):
            print("레포지토리 클론에 실패했습니다.")
            return
        
        # 3. 클론된 폴더 확인
        project_folder = repo_name
        if not os.path.exists(project_folder):
            print(f"❌ 클론된 폴더를 찾을 수 없습니다: {project_folder}")
            return
        
        # 4. 출력 파일명 입력받기
        output_filename = get_output_filename()
        
        # 5. 프로젝트 분석 및 결과 저장
        save_analysis_result(project_folder, output_filename)
        
        # 6. 클론된 폴더 삭제
        cleanup_folder(project_folder)
        
        print("\n" + "=" * 50)
        print("🎉 모든 작업이 완료되었습니다!")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 프로그램이 사용자에 의해 중단되었습니다.")
        # 중단 시에도 폴더 정리
        if project_folder and os.path.exists(project_folder):
            cleanup_folder(project_folder)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        # 오류 시에도 폴더 정리
        if project_folder and os.path.exists(project_folder):
            cleanup_folder(project_folder)

if __name__ == "__main__":
    main()

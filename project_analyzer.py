#!/usr/bin/env python3
"""
改进版项目目录分析工具
自动排除虚拟环境、缓存等无关目录，增强项目类型检测
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict


class ProjectAnalyzer:
    """项目分析器"""

    # 全局排除列表（关键：自动过滤无关目录）
    DEFAULT_EXCLUDE_DIRS = {
        # 虚拟环境/包管理
        '.venv', 'venv', 'env', '.env', 'virtualenv', 'venv*', 'env*',
        'node_modules', '.npm', '.yarn',
        '__pypackages__', '.poetry',
        # 版本控制
        '.git', '.svn', '.hg',
        # 构建输出/缓存
        '__pycache__', '.pyc', '.pyo', '.pyd', '.so', '.dll',
        'build', 'dist', 'out', 'target', 'bin', 'obj',
        '.cache', '.mypy_cache', '.pytest_cache', '.ruff_cache',
        # IDE/编辑器
        '.idea', '.vscode', '.vs', '.settings',
        '*.swp', '*.swo', '*~',
        # 系统/隐藏文件
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        # 依赖锁定文件（通常不展示内容）
        'package-lock.json', 'yarn.lock', 'poetry.lock', 'pipfile.lock'
    }

    # 项目类型特征文件
    PROJECT_MARKERS = {
        'Python': ['requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg', 'Pipfile', 'poetry.lock'],
        'Node.js': ['package.json', 'package-lock.json', 'yarn.lock'],
        'Java': ['pom.xml', 'build.gradle', 'build.gradle.kts', 'settings.gradle'],
        'Go': ['go.mod', 'go.sum'],
        'Rust': ['Cargo.toml', 'Cargo.lock'],
        'Ruby': ['Gemfile', 'Gemfile.lock'],
        'PHP': ['composer.json', 'composer.lock'],
        'Docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
        '前端': ['vite.config.js', 'webpack.config.js', 'angular.json', 'vue.config.js'],
        '配置': ['.gitignore', '.dockerignore', '.env.example', 'Makefile']
    }

    def __init__(self, project_path):
        self.root = Path(project_path).resolve()
        if not self.root.exists():
            raise ValueError(f"路径不存在: {project_path}")

    def analyze(self, max_depth=4, output_format='tree', show_hidden=False):
        """执行分析"""
        print(f"🔍 分析项目: {self.root}")
        print(f"📁 项目类型: {self._detect_project_type()}")
        print("=" * 60)

        if output_format == 'tree':
            self._print_tree(max_depth, show_hidden)
        elif output_format == 'flat':
            self._print_flat(max_depth, show_hidden)
        elif output_format == 'summary':
            self._print_summary()
        elif output_format == 'json':
            self._print_json(max_depth, show_hidden)

    def _detect_project_type(self):
        """检测项目类型（增强版）"""
        markers_found = defaultdict(list)

        for proj_type, markers in self.PROJECT_MARKERS.items():
            for marker in markers:
                if (self.root / marker).exists():
                    markers_found[proj_type].append(marker)

        if markers_found:
            # 按找到的标记数量排序
            sorted_types = sorted(markers_found.items(), key=lambda x: len(x[1]), reverse=True)
            primary_type = sorted_types[0][0]

            details = []
            for proj_type, markers in sorted_types[:3]:  # 取前3个类型
                details.append(f"{proj_type}({len(markers)})")

            return f"{primary_type}项目 [检测到: {', '.join(details)}]"

        # 通过文件扩展名推断
        ext_counts = defaultdict(int)
        for ext in ['.py', '.js', '.java', '.go', '.rs', '.php', '.rb', '.html', '.css']:
            count = len(list(self.root.rglob(f'*{ext}')))
            if count > 0:
                ext_counts[ext] = count

        if ext_counts:
            main_ext = max(ext_counts.items(), key=lambda x: x[1])
            lang_map = {
                '.py': 'Python', '.js': 'JavaScript', '.java': 'Java',
                '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
                '.rb': 'Ruby', '.html': 'Web', '.css': 'Web'
            }
            lang = lang_map.get(main_ext[0], main_ext[0])
            return f"{lang}项目 (基于文件扩展名推断)"

        return "通用项目"

    def _should_exclude(self, path, is_dir, depth, max_depth, show_hidden):
        """判断是否应排除路径"""
        # 深度限制
        if depth > max_depth:
            return True

        # 隐藏文件处理
        if not show_hidden and path.name.startswith('.'):
            # 但允许顶级配置文件
            if depth > 1 or path.name not in ['.gitignore', '.env.example']:
                return True

        # 排除特定目录
        if is_dir:
            for exclude_pattern in self.DEFAULT_EXCLUDE_DIRS:
                if exclude_pattern.endswith('*'):
                    # 通配符匹配
                    if path.name.startswith(exclude_pattern[:-1]):
                        return True
                elif path.name == exclude_pattern:
                    return True

        return False

    def _print_tree(self, max_depth, show_hidden):
        """打印树状结构"""
        print("🌳 项目结构 (已过滤无关目录):")
        print()

        def print_item(path, prefix="", depth=0, is_last=False):
            # 获取相对于根目录的显示名
            if path == self.root:
                display_name = "."
                is_dir = True
            else:
                display_name = path.name
                is_dir = path.is_dir()

            # 检查是否排除
            if self._should_exclude(path, is_dir, depth, max_depth, show_hidden):
                return

            # 打印当前项
            if depth == 0:
                print(f"{display_name}/")
            else:
                connector = "└── " if is_last else "├── "
                item_type = "/" if is_dir else ""
                # 为文件类型添加颜色/标识
                if not is_dir:
                    ext_color = {
                        '.py': '[Py]', '.js': '[JS]', '.ts': '[TS]',
                        '.json': '[JSON]', '.yaml': '[YAML]', '.yml': '[YAML]',
                        '.md': '[MD]', '.txt': '[TXT]', '.html': '[HTML]'
                    }.get(path.suffix.lower(), '')
                    display_name = f"{display_name} {ext_color}"

                print(f"{prefix}{connector}{display_name}{item_type}")

            # 递归处理目录
            if is_dir and depth < max_depth:
                try:
                    # 获取并排序子项
                    children = sorted(path.iterdir(),
                                      key=lambda x: (not x.is_dir(), x.name.lower()))

                    # 过滤子项
                    children = [c for c in children
                                if not self._should_exclude(c, c.is_dir(), depth + 1, max_depth, show_hidden)]

                    for i, child in enumerate(children):
                        is_last_child = (i == len(children) - 1)
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        print_item(child, new_prefix, depth + 1, is_last_child)

                except PermissionError:
                    pass

        print_item(self.root)

    def _print_summary(self):
        """打印项目摘要"""
        print("📊 项目摘要:")
        print()

        # 统计各类文件
        file_stats = defaultdict(int)
        dir_stats = defaultdict(int)

        for path in self.root.rglob('*'):
            if self._should_exclude(path, path.is_dir(), 0, 10, False):
                continue

            if path.is_file():
                ext = path.suffix.lower()
                if ext:
                    file_stats[ext] += 1
                else:
                    file_stats['[无扩展名]'] += 1
            else:
                dir_stats[path.name] += 1

        print("📈 文件类型统计:")
        for ext, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            type_name = {
                '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                '.java': 'Java', '.go': 'Go', '.rs': 'Rust',
                '.html': 'HTML', '.css': 'CSS', '.json': 'JSON',
                '.yaml': 'YAML', '.yml': 'YAML', '.md': 'Markdown'
            }.get(ext, ext)
            print(f"  {type_name:15} {count:4} 个文件")

        print()
        print("📁 主要目录:")
        for dir_name, count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {dir_name}/")

    def _print_flat(self, max_depth, show_hidden):
        """扁平化输出关键文件"""
        print("📄 关键文件列表:")
        print()

        key_files = []
        for path in self.root.rglob('*'):
            if self._should_exclude(path, path.is_dir(), 0, max_depth, show_hidden):
                continue

            if path.is_file():
                # 只显示重要文件类型
                important_exts = {'.py', '.js', '.ts', '.java', '.go', '.rs',
                                  '.php', '.rb', '.html', '.css', '.json', '.yaml',
                                  '.yml', '.md', '.txt', '.ini', '.cfg', '.toml'}
                if path.suffix in important_exts:
                    rel_path = path.relative_to(self.root)
                    if len(rel_path.parts) <= max_depth + 1:
                        key_files.append(str(rel_path))

        # 按目录分组显示
        grouped = defaultdict(list)
        for file_path in sorted(key_files):
            parts = file_path.split('/')
            if len(parts) > 1:
                dir_name = '/'.join(parts[:-1])
                grouped[dir_name].append(parts[-1])
            else:
                grouped['.'].append(file_path)

        for directory, files in sorted(grouped.items()):
            print(f"📂 {directory}/")
            for file in files[:10]:  # 每个目录最多显示10个文件
                print(f"   ├── {file}")
            if len(files) > 10:
                print(f"   └── ... 还有 {len(files) - 10} 个文件")
            print()

    def _print_json(self, max_depth, show_hidden):
        """JSON格式输出"""

        def path_to_dict(path, depth=0):
            if self._should_exclude(path, path.is_dir(), depth, max_depth, show_hidden):
                return None

            item = {
                'name': path.name,
                'type': 'directory' if path.is_dir() else 'file',
                'path': str(path.relative_to(self.root))
            }

            if path.is_file():
                item.update({
                    'size': path.stat().st_size,
                    'extension': path.suffix,
                    'modified': path.stat().st_mtime
                })
            else:
                children = []
                try:
                    for child in sorted(path.iterdir(), key=lambda x: x.name.lower()):
                        child_data = path_to_dict(child, depth + 1)
                        if child_data:
                            children.append(child_data)
                except PermissionError:
                    pass

                item['children'] = children
                item['child_count'] = len(children)

            return item

        result = path_to_dict(self.root)
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='改进版项目目录分析工具')
    parser.add_argument('path', nargs='?', default='.', help='项目路径 (默认: 当前目录)')
    parser.add_argument('--depth', type=int, default=4, help='目录深度限制 (默认: 4)')
    parser.add_argument('--format', choices=['tree', 'flat', 'summary', 'json'],
                        default='tree', help='输出格式 (默认: tree)')
    parser.add_argument('--show-hidden', action='store_true',
                        help='显示隐藏文件和目录')
    parser.add_argument('--no-exclude', action='store_true',
                        help='禁用自动排除（显示所有文件）')

    args = parser.parse_args()

    try:
        analyzer = ProjectAnalyzer(args.path)

        # 如果禁用排除，清空排除列表
        if args.no_exclude:
            analyzer.DEFAULT_EXCLUDE_DIRS.clear()

        analyzer.analyze(
            max_depth=args.depth,
            output_format=args.format,
            show_hidden=args.show_hidden
        )

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
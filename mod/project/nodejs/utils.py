import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

def test_registry_url() -> Tuple[Optional[str], Optional[str]]:
    mirrors = [
        {"name": "Official", "url": "https://registry.npmjs.org/"},
        {"name": "GitHub Packages", "url": "https://npm.pkg.github.com/"},
        {"name": "Yarn", "url": "https://registry.yarnpkg.com/"},
        {"name": "Cloudflare", "url": "https://registry.npmjs.cf/"},
        {"name": "npmmirror_Chinese", "url": "https://registry.npmmirror.com/"},
        {"name": "Huawei", "url": "https://mirrors.huaweicloud.com/repository/npm/"},
        {"name": "Tencent", "url": "https://mirrors.cloud.tencent.com/npm/"}
    ]

    def test_mirror(mirror) -> Optional[Tuple[str, str]]:
        try:
            # 使用 -/ping 测试镜像源是否可用, 避免部分镜像源不支持web访问 如：腾讯源
            response = requests.get(mirror["url"] + "-/ping", timeout=5)
            if response.status_code == 200:
                return mirror["name"], mirror["url"]
        except Exception as e:
            pass
        return None

    executor = ThreadPoolExecutor(max_workers=4)
    futures = {executor.submit(test_mirror, mirror): mirror for mirror in mirrors}

    for future in as_completed(futures):
        result: Optional[Tuple[str, str]] = future.result()
        if result:
            executor.shutdown(wait=False)
            return result

    return None, None
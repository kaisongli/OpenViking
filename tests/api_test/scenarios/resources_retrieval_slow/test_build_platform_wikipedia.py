from build_test_helpers import (
    _extract_error_message,
    assert_resource_indexed,
    assert_root_uri_valid,
    assert_source_format,
)


class TestBuildPlatformWikipedia:
    """TC-P05 Wikipedia 平台 URL 构建测试"""

    def test_build_wikipedia_page(self, api_client):
        """TC-P05 Wikipedia页面构建：验证 wikipedia.org URL 走 WEBPAGE 路由且内容可检索（CI环境Wikipedia可能403）"""
        wiki_url = "https://en.wikipedia.org/wiki/Software_testing"

        response = api_client.add_resource(path=wiki_url, wait=True)
        assert response.status_code == 200

        data = response.json()
        if data.get("status") == "error":
            error_msg = _extract_error_message(data).lower()
            if "403" in error_msg or "forbidden" in error_msg or "blocked" in error_msg:
                print("✓ TC-P05 Wikipedia页面构建跳过(CI环境Wikipedia返回403)")
                return
            raise AssertionError(f"Wikipedia页面构建失败: {error_msg}")

        assert data.get("status") == "ok"

        result = data.get("result", {})
        if isinstance(result, dict) and result.get("status") == "error":
            inner_errors = result.get("errors", [])
            inner_msg = " ".join(str(e) for e in inner_errors).lower()
            if "403" in inner_msg or "forbidden" in inner_msg:
                print("✓ TC-P05 Wikipedia页面构建跳过(CI环境Wikipedia返回403)")
                return
            raise AssertionError(f"Wikipedia页面构建内层错误: {inner_msg}")

        root_uri = result.get("root_uri")
        assert root_uri, "Wikipedia页面构建应返回root_uri, 实际为空"
        assert_root_uri_valid(root_uri)

        meta = result.get("meta", {})
        assert meta.get("url_type") in ("webpage", "download_text", "download_html", None), (
            f"meta.url_type 应为 webpage/download_text/download_html, 实际: {meta.get('url_type')}"
        )

        assert_source_format(api_client, root_uri, ["html", "markdown"])

        stat_resp = api_client.fs_stat(root_uri)
        assert stat_resp.status_code == 200

        assert_resource_indexed(api_client, root_uri, "software testing")

        print(f"✓ TC-P05 Wikipedia页面构建通过, root_uri: {root_uri}")

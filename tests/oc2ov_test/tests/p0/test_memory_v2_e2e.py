"""
P0 - Memory V2 端到端验证测试
测试目标：验证 Memory V2 功能正确生成记忆文件
测试场景：发送用户信息 -> 执行 /compact -> 验证记忆文件新增 -> 验证记忆检索
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Set

from base_cli_test import BaseOpenClawCLITest


class TestMemoryV2E2E(BaseOpenClawCLITest):
    """
    Memory V2 端到端验证测试
    测试目标：验证 Memory V2 功能正确生成记忆文件
    测试场景：发送用户信息 -> 执行 /compact -> 验证记忆文件新增 -> 验证记忆检索
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.memory_base_path = Path("/Users/bytedance/PycharmProjects/OpenViking/.openviking_data")
        cls.memory_dir = cls.memory_base_path / "viking" / "default" / "user" / "default" / "memories"
        cls.files_before: Set[str] = set()
        cls.files_after: Set[str] = set()

    def _get_memory_files(self) -> Set[str]:
        """获取当前所有记忆文件的相对路径集合"""
        if not self.memory_dir.exists():
            return set()

        files = set()
        for f in self.memory_dir.rglob("*.md"):
            if not f.name.startswith('.'):
                files.add(str(f.relative_to(self.memory_dir)))
        return files

    def _record_files_before(self):
        """记录测试前的记忆文件状态"""
        self.files_before = self._get_memory_files()

        entities_count = len([f for f in self.files_before if f.startswith('entities/')])
        events_count = len([f for f in self.files_before if f.startswith('events/')])
        preferences_count = len([f for f in self.files_before if f.startswith('preferences/')])
        profile_count = len([f for f in self.files_before if f == 'profile.md'])

        self.logger.info("测试前记忆文件统计:")
        self.logger.info(f"  - entities: {entities_count} 个文件")
        self.logger.info(f"  - events: {events_count} 个文件")
        self.logger.info(f"  - preferences: {preferences_count} 个文件")
        self.logger.info(f"  - profile: {profile_count} 个文件")
        self.logger.info(f"  - 总计: {len(self.files_before)} 个文件")

    def _verify_memory_files(self) -> int:
        """验证记忆文件存储及新增文件，返回新增文件数"""
        self.files_after = self._get_memory_files()

        new_files = self.files_after - self.files_before
        deleted_files = self.files_before - self.files_after

        self.logger.info("文件变化统计:")
        self.logger.info(f"  - 测试前文件数: {len(self.files_before)}")
        self.logger.info(f"  - 测试后文件数: {len(self.files_after)}")
        self.logger.info(f"  - 新增文件数: {len(new_files)}")
        self.logger.info(f"  - 删除文件数: {len(deleted_files)}")

        if new_files:
            self.logger.info("新增的记忆文件:")
            for f in sorted(new_files):
                file_path = self.memory_dir / f
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                self.logger.info(f"  + {f} (修改时间: {mtime.strftime('%H:%M:%S')})")
        else:
            self.logger.warning("未检测到新增的记忆文件")

        return len(new_files)

    def test_memory_v2_e2e(self):
        """测试场景：Memory V2 端到端验证"""
        test_id = int(time.time())

        self.logger.info("[1/5] 记录测试前的记忆文件状态")
        self._record_files_before()

        self.logger.info("[2/5] 发送测试消息：写入用户信息")
        test_message = f"我是测试用户李四，我喜欢游泳和摄影，我的测试编号是{test_id}"
        response1 = self.send_and_log(test_message)

        self.logger.info("[3/5] 执行 /compact 指令触发记忆提取")
        response2 = self.send_and_log("/compact")

        self.logger.info("等待记忆提取完成...")
        self.wait_for_sync(10)

        self.logger.info("[4/5] 验证记忆文件存储及新增文件")
        new_files_count = self._verify_memory_files()
        self.assertGreater(new_files_count, 0, "应该至少新增一个记忆文件")

        self.logger.info("[5/5] 验证记忆检索：询问用户信息")
        self.logger.info("询问前一次对话内容...")
        response3 = self.send_and_log("你还记得我的名字和爱好吗？")

        self.logger.info("验证关键词...")
        self.assertAnyKeywordInResponse(
            response3, [["李四"], ["游泳"], ["摄影"], ["测试"]], case_sensitive=False
        )

        self.logger.info("=" * 60)
        self.logger.info("Memory V2 端到端测试通过")
        self.logger.info(f"新增 {new_files_count} 个记忆文件")
        self.logger.info("=" * 60)

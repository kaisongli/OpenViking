"""
P0 - 记忆结构化写入验证测试
测试目标：验证OpenViking能正确接收、存储OpenClaw传入的用户信息
"""

from tests.base_cli_test import BaseOpenClawCLITest


class TestMemoryWriteGroupA(BaseOpenClawCLITest):
    """
    测试组A（小明）：基本记忆结构化写入验证
    测试目标：验证OpenViking能正确接收、存储OpenClaw传入的用户信息，无数据丢失
    测试场景：写入小明的基本信息（姓名、年龄、地区、职业），然后验证信息正确性
    """
    
    def test_memory_write_basic_info(self):
        """测试场景：基本信息写入与验证"""
        self.logger.info("[1/4] 发送记忆写入指令")
        message = "我叫小明，今年30岁，住在华东区，职业是测试开发"
        response1 = self.send_and_log(message)
        
        self.wait_for_sync()
        
        self.logger.info("[3/4] 发送确认指令：我是谁")
        response2 = self.send_and_log("我是谁")
        
        self.assertAnyKeywordInResponse(
            response2,
            [["小明", "测试开发", "30岁", "华东"]],
            case_sensitive=False
        )
        
        self.logger.info("[4/4] 再等待后询问年龄...")
        self.wait_for_sync()
        
        response3 = self.send_and_log("我当前多少岁")
        
        self.assertAnyKeywordInResponse(
            response3,
            [["30", "三十"]],
            case_sensitive=False
        )
        
        self.logger.info("测试组A执行完成")


class TestMemoryWriteGroupB(BaseOpenClawCLITest):
    """
    测试组B（小红）：更多维度信息写入
    测试目标：多维度丰富信息写入验证
    测试场景：写入小红的详细信息（姓名、年龄、地址、职业、喜好、生日）
    """
    
    def test_memory_write_rich_info(self):
        """测试场景：丰富信息写入与验证"""
        message = (
            "我叫小红，今年25岁，住在华北区北京市朝阳区，职业是产品经理，"
            "喜欢美食和旅游，不喜欢加班，我的生日是1999年8月15日"
        )
        self.logger.info("[1/3] 发送丰富信息记忆写入")
        response1 = self.send_and_log(message)
        
        self.wait_for_sync()
        
        self.logger.info("[3/3] 验证多维度信息：询问我的职业、生日和喜好")
        response2 = self.send_and_log("我的职业是什么，生日是什么时候，我喜欢什么")
        
        self.assertAnyKeywordInResponse(
            response2,
            [
                ["产品经理"],
                ["1999", "8月", "8/15"],
                ["美食", "旅游"]
            ],
            case_sensitive=False
        )
        
        self.logger.info("测试组B执行完成")


class TestMemoryPersistence(BaseOpenClawCLITest):
    """
    记忆跨会话读取验证
    测试目标：验证OpenClaw重启后，可从OpenViking正常读取历史记忆，记忆持久化生效
    测试场景：写入用户信息，使用不同session-id模拟新会话，验证记忆读取
    """
    
    def test_memory_persistence_group_a(self):
        """测试组A：我喜欢吃樱桃，日常喜欢喝美式咖啡"""
        self.logger.info("[1/5] 测试组A - 写入记忆信息")
        message = "我喜欢吃樱桃，日常喜欢喝美式咖啡"
        session_a = "persistence_test_a"
        
        response1 = self.send_and_log(message, session_id=session_a)
        self.wait_for_sync()
        
        self.logger.info("[2/5] 验证当前会话能读取记忆")
        response2 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_a)
        self.assertAnyKeywordInResponse(
            response2,
            [["樱桃"], ["美式", "咖啡"]],
            case_sensitive=False
        )
        
        self.logger.info("[3/5] 使用新的 session-id 模拟新会话")
        session_b = "persistence_test_b"
        
        self.wait_for_sync()
        
        self.logger.info("[4/5] 在新会话中查询记忆")
        response3 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_b)
        
        self.logger.info("[5/5] 验证记忆持久化读取")
        self.assertAnyKeywordInResponse(
            response3,
            [["樱桃"], ["美式", "咖啡"]],
            case_sensitive=False
        )
        
        self.logger.info("测试组A执行完成")
    
    def test_memory_persistence_group_b(self):
        """测试组B：我喜欢吃芒果，日常喜欢喝拿铁咖啡"""
        self.logger.info("[1/5] 测试组B - 写入记忆信息")
        message = "我喜欢吃芒果，日常喜欢喝拿铁咖啡"
        session_c = "persistence_test_c"
        
        response1 = self.send_and_log(message, session_id=session_c)
        self.wait_for_sync()
        
        self.logger.info("[2/5] 验证当前会话能读取记忆")
        response2 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_c)
        self.assertAnyKeywordInResponse(
            response2,
            [["芒果"], ["拿铁", "咖啡"]],
            case_sensitive=False
        )
        
        self.logger.info("[3/5] 使用新的 session-id 模拟新会话")
        session_d = "persistence_test_d"
        
        self.wait_for_sync()
        
        self.logger.info("[4/5] 在新会话中查询记忆")
        response3 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_d)
        
        self.logger.info("[5/5] 验证记忆持久化读取")
        self.assertAnyKeywordInResponse(
            response3,
            [["芒果"], ["拿铁", "咖啡"]],
            case_sensitive=False
        )
        
        self.logger.info("测试组B执行完成")
    
    def test_memory_persistence_group_c(self):
        """测试组C：我喜欢吃草莓，日常喜欢喝抹茶拿铁"""
        self.logger.info("[1/5] 测试组C - 写入记忆信息")
        message = "我喜欢吃草莓，日常喜欢喝抹茶拿铁"
        session_e = "persistence_test_e"
        
        response1 = self.send_and_log(message, session_id=session_e)
        self.wait_for_sync()
        
        self.logger.info("[2/5] 验证当前会话能读取记忆")
        response2 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_e)
        self.assertAnyKeywordInResponse(
            response2,
            [["草莓"], ["抹茶", "拿铁"]],
            case_sensitive=False
        )
        
        self.logger.info("[3/5] 使用新的 session-id 模拟新会话")
        session_f = "persistence_test_f"
        
        self.wait_for_sync()
        
        self.logger.info("[4/5] 在新会话中查询记忆")
        response3 = self.send_and_log("我喜欢吃什么水果？平时爱喝什么？", session_id=session_f)
        
        self.logger.info("[5/5] 验证记忆持久化读取")
        self.assertAnyKeywordInResponse(
            response3,
            [["草莓"], ["抹茶", "拿铁"]],
            case_sensitive=False
        )
        
        self.logger.info("测试组C执行完成")

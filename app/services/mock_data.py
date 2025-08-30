from typing import Any, Optional
import uuid
import time
import random
import json
import os

class MockDataService:
    """模拟数据服务"""
    
    def __init__(self):
        """初始化模拟数据"""
        self.users: dict[str, dict[str, Any]] = {}
        self.cards: dict[str, dict[str, Any]] = {}
        self.matches: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, list[dict[str, Any]]] = {}
        self.sms_codes: dict[str, dict[str, Any]] = {}
        
        # 用户数据本地存储文件路径
        self.user_data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_user_data.json")
        
        # 初始化一些测试数据
        self._init_test_data()
        
        # 尝试从本地文件加载用户数据
        self._load_user_data_from_file()
    
    def _load_fixed_housing_data(self):
        """加载固定的房源测试数据"""
        try:
            # 获取项目根目录下的测试数据文件
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            json_file_path = os.path.join(current_dir, "fixed_housing_test_data.json")
            
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load fixed housing data: {e}")
        
        return None
    
    def _load_user_data_from_file(self):
        """从本地文件加载用户数据"""
        try:
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                    # 更新内存中的用户数据
                    for user_id, user in user_data.items():
                        self.users[user_id] = user
                    print(f"Loaded user data from {self.user_data_file}")
        except Exception as e:
            print(f"Warning: Could not load user data from file: {e}")
    
    def _save_user_data_to_file(self):
        """将用户数据保存到本地文件"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
                print(f"Saved user data to {self.user_data_file}")
        except Exception as e:
            print(f"Warning: Could not save user data to file: {e}")

    def _init_test_data(self):
        """初始化测试数据"""
        # 尝试加载固定的房源测试数据
        fixed_data = self._load_fixed_housing_data()
        
        if fixed_data:
            # 加载固定的测试用户
            for user_data in fixed_data.get("testUsers", []):
                self.create_user(user_data)
            
            # 加载固定的房源卡片
            for card_data in fixed_data.get("housingCards", []):
                # 确保包含 videoUrl
                if "houseInfo" in card_data and "videoUrl" not in card_data["houseInfo"]:
                    card_data["houseInfo"]["videoUrl"] = "https://cdn.pixabay.com/video/2024/02/03/199109-909564730_tiny.mp4"
                self.cards[card_data["id"]] = card_data
            
            # 加载固定的匹配数据
            for match_data in fixed_data.get("matches", []):
                self.matches[match_data["id"]] = match_data
        
        # 创建默认测试用户（如果没有加载到固定数据）
        if "user_001" not in self.users:
            test_user = self.create_user({
                "id": "user_001",
                "nickName": "小明",
                "avatarUrl": "https://picsum.photos/200/200?random=avatar1",
                "gender": 1,
                "age": 25,
                "occupation": "软件工程师",
                "location": ["北京市", "朝阳区"],
                "bio": "喜欢编程和旅行",
                "matchType": "dating",
                "userRole": "seeker",
                "interests": ["编程", "旅行", "音乐"],
                "preferences": {
                    "ageRange": [25, 35],
                    "distance": 10
                },
                "phone": "13800138001",
                "email": "xiaoming@example.com",
                "education": "本科",
                "joinDate": int(time.time())
            })
        
        # 创建另一个测试用户（用于测试获取用户资料）
        if "card_001" not in self.users:
            self.create_user({
                "id": "card_001",
                "nickName": "测试卡片用户",
                "avatarUrl": "https://picsum.photos/200/200?random=avatar2",
                "gender": 2,
                "age": 26,
                "occupation": "设计师",
                "location": "上海市 上海市 徐汇区",
                "bio": "喜欢设计和摄影",
                "matchType": "dating",
                "userRole": "provider",
                "interests": ["设计", "摄影", "旅行"],
                "preferences": {
                    "ageRange": [25, 35],
                    "distance": 15
                }
            })
        
        # 创建test_user_001用户（用于认证测试）
        if "test_user_001" not in self.users:
            self.create_user({
                "id": "test_user_001",
                "phone": "13800138000",
                "nickName": "测试11用户",
                "avatarUrl": "https://picsum.photos/200/200?random=100",
                "gender": 1,
                "age": 30,
                "occupation": "软件工程师",
                "location": ["上海市", "上海市", "徐汇区"],
                "bio": "这是一个测试账号，用于开发和测试微信小程序",
                "education": "本科",
                "interests": ["编程", "测试", "开发"],
                "joinDate": 1628553600,
                "email": "test@example.com",
                "matchType": "dating",
                "userRole": "user",
                "preferences": {
                    "ageRange": [25, 35],
                    "distance": 20
                }
            })
        
        # 如果没有房源卡片，创建一些默认的
        housing_cards = [card for card in self.cards.values() if card.get("matchType") == "housing"]
        if not housing_cards:
            for i in range(1, 4):
                card_id = f"card_house_default_{i:03d}"
                self.create_card({
                    "id": card_id,
                    "name": f"精装房源{i}",
                    "avatar": f"https://picsum.photos/200/200?random=house{i}",
                    "age": None,
                    "occupation": "房源",
                    "distance": f"{random.randint(1, 15)}km",
                    "interests": [],
                    "matchType": "housing",
                    "userRole": "seeker",
                    "bio": f"这是测试房源{i}的详细描述",
                    "houseInfo": {
                        "price": 3000 + i * 500,
                        "area": 60 + i * 10,
                        "rooms": 2,
                        "location": "北京市朝阳区",
                        "features": ["近地铁", "精装修", "家电齐全"],
                        "videoUrl": "https://cdn.pixabay.com/video/2024/02/03/199109-909564730_tiny.mp4"
                    }
                })
        
        # 创建默认匹配记录（如果没有）
        if not self.matches:
            self.matches["match_001"] = {
                "id": "match_001",
                "userId1": "user_001",
                "userId2": "card_001",
                "reason": "你们有共同的兴趣",
                "createTime": int(time.time()),
                "isRead": False,
                "type": "dating",
                "status": "matched"
            }
        
        # 创建测试消息
        if "match_001" not in self.messages:
            self.messages["match_001"] = []
            self.send_message("match_001", "user_001", "你好，很高兴认识你！", "text")
            self.send_message("match_001", "card_001", "你好，我也很高兴认识你！", "text")
    
    def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """创建用户"""
        user_id = user_data.get("id") or str(uuid.uuid4())
        user = {
            "id": user_id,
            **user_data
        }
        print(f"DEBUG: Creating user with ID: {user_id}")
        self.users[user_id] = user
        print(f"DEBUG: Users after creation: {list(self.users.keys())}")
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        """根据ID获取用户"""
        print(f"DEBUG: Looking for user_id: {user_id}")
        print(f"DEBUG: Available users: {list(self.users.keys())}")
        result = self.users.get(user_id)
        print(f"DEBUG: Found user: {result is not None}")
        return result
    
    def get_user_by_token(self, token: str) -> Optional[dict[str, Any]]:
        """根据token获取用户信息（测试模式）"""
        # 测试模式下，token就是用户ID
        # 支持测试用例中的token
        if token == "user_001":
            return self.users.get("user_001")
        elif token == "invalid_token":
            return None
        else:
            return self.users.get(token)
    
    def update_profile(self, user_id: str, profile_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """更新用户资料"""
        print(f"DEBUG: MockDataService.update_profile called")
        print(f"DEBUG: user_id={user_id}, profile_data={profile_data}")
        
        user = self.get_user_by_id(user_id)
        if not user:
            print(f"DEBUG: User {user_id} not found")
            return None  # Return None to indicate user not found
        
        print(f"DEBUG: Before update: avatarUrl={user.get('avatarUrl', 'NOT_FOUND')}")
        
        # 更新字段
        user.update(profile_data)
        
        print(f"DEBUG: After update: avatarUrl={user.get('avatarUrl', 'NOT_FOUND')}")
        print(f"DEBUG: Updated user data: {user}")
        
        # 将更新后的用户数据保存到本地文件
        self._save_user_data_to_file()
        
        return user
    
    def create_card(self, card_data: dict[str, Any]) -> dict[str, Any]:
        """创建卡片"""
        card_id = card_data.get("id") or str(uuid.uuid4())
        card = {
            "id": card_id,
            **card_data
        }
        
        # 为租客用户场景添加 videoUrl 字段
        if card_data.get("matchType") == "housing" and card_data.get("userRole") == "seeker":
            if "videoUrl" not in card:
                card["videoUrl"] = random.choice([
                    "https://cdn.pixabay.com/video/2024/02/03/199109-909564730_tiny.mp4",
                    "https://cdn.pixabay.com/video/2023/04/08/157989-815894934_tiny.mp4",
                    "https://cdn.pixabay.com/video/2023/09/30/183008-869941724_tiny.mp4",
                    "https://cdn.pixabay.com/video/2025/03/21/266435_tiny.mp4",
                    "https://cdn.pixabay.com/video/2021/08/30/86867-594991237_tiny.mp4",
                    "https://cdn.pixabay.com/video/2025/06/13/285663_tiny.mp4"
                ])
        
        self.cards[card_id] = card
        return card
    
    def get_cards(self, match_type: str, user_role: str, page: int, page_size: int) -> dict[str, Any]:
        """获取匹配卡片"""
        # 对于房源匹配，seeker用户应该看到所有房源卡片（不管房源的userRole）
        if match_type == "housing":
            filtered_cards = [
                card for card in self.cards.values()
                if card.get("matchType") == match_type
            ]
        else:
            # 对于其他类型的匹配，按原逻辑过滤
            filtered_cards = [
                card for card in self.cards.values()
                if card.get("matchType") == match_type and card.get("userRole") == user_role
            ]
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            "total": len(filtered_cards),
            "list": filtered_cards[start:end],
            "page": page,
            "pageSize": page_size
        }
    
    def create_match(self, user_id: str, card_id: str, action: str) -> dict[str, Any]:
        """创建匹配"""
        # 在实际应用中，需要检查用户是否已经对该卡片进行过操作
        
        # 模拟匹配逻辑
        is_match = action == "like" and random.random() > 0.5
        
        result = {
            "isMatch": is_match,
            "matchId": None
        }
        
        if is_match:
            match_id = str(uuid.uuid4())
            match = {
                "id": match_id,
                "userId1": user_id,
                "userId2": card_id,
                "reason": "你们有共同的兴趣",
                "createTime": int(time.time()),
                "isRead": False,
                "type": "dating",
                "status": "matched"
            }
            self.matches[match_id] = match
            result["matchId"] = match_id
            
            # 初始化消息列表
            self.messages[match_id] = []
        
        return result
    
    def get_matches(self, status: str = None, match_type: str = None, page: int = 1, page_size: int = 10):
        """获取匹配列表数据 - 支持API查询参数"""
        matches = []
        
        # 使用枚举值生成数据
        from app.models.enums import MatchStatus, MatchType, Region, Interest, Education, HouseType, ActivityType
        
        # 生成不同状态和类型的匹配数据
        statuses = [status.value for status in MatchStatus]
        match_types = [mtype.value for mtype in MatchType if mtype != MatchType.BUSINESS]  # 排除商务类型
        
        for i in range(1, 51):  # 生成50条匹配数据
            match_status = statuses[(i - 1) % len(statuses)]
            match_type_val = match_types[(i - 1) % len(match_types)]
            
            # 状态筛选
            if status and status != "null" and match_status != status:
                continue
                
            # 类型筛选
            if match_type and match_type_val != match_type:
                continue
            
            match_data = {
                "id": f"match_{i:03d}",
                "user1_id": "test_user_001",
                "user2_id": f"test_user_{(i % 4) + 2:03d}",
                "match_type": match_type_val,
                "status": match_status,
                "score": round(0.5 + (i % 50) / 100, 2),
                "is_active": True,
                "created_at": f"2024-11-{(i % 28) + 1:02d}T08:00:00Z",
                "updated_at": f"2024-11-{(i % 28) + 1:02d}T08:00:00Z",
                "user1": {
                    "id": "test_user_001",
                    "username": "test_user_001",
                    "nick_name": "测试用户001",
                    "avatar_url": "https://example.com/avatar1.jpg"
                },
                "user2": {
                    "id": f"test_user_{(i % 4) + 2:03d}",
                    "username": f"test_user_{(i % 4) + 2:03d}",
                    "nick_name": f"测试用户{(i % 4) + 2:03d}",
                    "avatar_url": f"https://example.com/avatar{(i % 4) + 2}.jpg"
                }
            }
            
            # 根据匹配类型添加特定字段，使用枚举值
            if match_type_val == "activity":
                activity_types = [atype.value for atype in ActivityType]
                regions = [region.value for region in Region]
                
                match_data.update({
                    "activity_id": f"activity_{1000 + i}",
                    "activity_name": f"{activity_types[i % len(activity_types)]}活动{i}",
                    "activity_type": activity_types[i % len(activity_types)],
                    "activity_location": f"{regions[i % len(regions)]}测试地点{i}",
                    "activity_time": f"2024-12-{(i % 28) + 1:02d}T10:00:00Z",
                    "skill_level": ["新手", "初级", "中级", "高级", "专家"][i % 5],
                    "group_size": ["1-2人", "3-5人", "5-10人", "10人以上"][i % 4],
                    "budget": ["免费", "0-100元", "100-300元", "300-500元", "500-1000元"][i % 5],
                    "message": f"这是第{i}条测试匹配消息" if i % 3 == 0 else None,
                    "expires_at": f"2024-12-{(i % 28) + 1:02d}T08:00:00Z"
                })
            elif match_type_val == "housing":
                house_types = [htype.value for htype in HouseType]
                regions = [region.value for region in Region]
                
                match_data.update({
                    "property_id": f"property_{1000 + i}",
                    "property_title": f"{house_types[i % len(house_types)]} - 测试房源{i}",
                    "house_type": house_types[i % len(house_types)],
                    "property_location": f"{regions[i % len(regions)]}测试小区{i}",
                    "rent_price": 2000 + i * 100,
                    "budget_range": ["1000-2000元", "2000-3000元", "3000-5000元", "5000-8000元", "8000元以上"][i % 5],
                    "decoration": ["精装修", "简装修", "毛坯房"][i % 3],
                    "facilities": ["空调", "洗衣机", "冰箱", "WiFi", "电视"][:((i % 5) + 1)],
                    "message": f"对这个房源很感兴趣" if i % 3 == 0 else None,
                    "expires_at": f"2024-12-{(i % 28) + 1:02d}T08:00:00Z"
                })
            else:  # dating
                educations = [edu.value for edu in Education]
                interests = [interest.value for interest in Interest]
                
                match_data.update({
                    "education": educations[i % len(educations)],
                    "interests": interests[:((i % 5) + 1)],
                    "income_range": ["5万以下", "5-10万", "10-20万", "20-30万", "30-50万", "50万以上"][i % 6],
                    "height_range": ["160-165", "165-170", "170-175", "175-180", "180-185"][i % 5],
                    "marital_status": ["未婚", "离异", "已婚"][i % 3],
                    "work_industry": ["互联网", "金融", "教育", "医疗", "服务业"][i % 5],
                    "message": f"很高兴认识你" if i % 3 == 0 else None,
                    "expires_at": f"2024-12-{(i % 28) + 1:02d}T08:00:00Z"
                })
            
            matches.append(match_data)
        
        # 分页处理
        total = len(matches)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_matches = matches[start_idx:end_idx]
        
        return {
            "list": paginated_matches,
            "total": total,
            "page": page,
            "pageSize": page_size
        }

    def get_matches_old(self, user_id: str, status: str, page: int, page_size: int) -> dict[str, Any]:
        """获取匹配列表 - 原有方法保持兼容性"""
        filtered_matches = []
        
        for match in self.matches.values():
            if match["userId1"] == user_id or match["userId2"] == user_id:
                if status == "all" or \
                   (status == "new" and not match["isRead"]) or \
                   (status == "contacted" and match["isRead"]):
                    # 添加卡片信息
                    other_user_id = match["userId2"] if match["userId1"] == user_id else match["userId1"]
                    card_info = self.cards.get(other_user_id, {}) or self.users.get(other_user_id, {})
                    match_with_card = {**match, "cardInfo": card_info}
                    filtered_matches.append(match_with_card)
        
        # 按创建时间排序
        filtered_matches.sort(key=lambda x: x["createTime"], reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            "total": len(filtered_matches),
            "list": filtered_matches[start:end],
            "page": page,
            "pageSize": page_size
        }
    
    def get_match_by_id(self, match_id: str, user_id: str = None) -> dict[str, Any]:
        """根据ID获取匹配"""
        match = self.matches.get(match_id)
        if not match:
            return {}  # Return empty dict instead of None
        
        # 添加卡片信息
        if user_id:
            other_user_id = match["userId2"] if match["userId1"] == user_id else match["userId1"]
        else:
            other_user_id = match["userId2"]  # 默认返回第二个用户的信息
            
        card_info = self.cards.get(other_user_id, {}) or self.users.get(other_user_id, {})
        return {**match, "cardInfo": card_info}
    
    def get_chat_history(self, match_id: str, page: int, page_size: int) -> dict[str, Any]:
        """获取聊天记录"""
        messages = self.messages.get(match_id, [])
        
        # 按时间排序
        messages.sort(key=lambda x: x["timestamp"], reverse=True)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        return {
            "total": len(messages),
            "list": messages[start:end],
            "page": page,
            "pageSize": page_size
        }
    
    def send_message(self, match_id: str, sender_id: str, content: str, msg_type: str) -> dict[str, Any]:
        """发送消息"""
        if match_id not in self.messages:
            self.messages[match_id] = []
        
        # 获取发送者信息
        sender = self.get_user_by_id(sender_id) or self.cards.get(sender_id, {})
        
        message = {
            "id": str(uuid.uuid4()),
            "content": content,
            "type": msg_type,
            "senderId": sender_id,
            "senderAvatar": sender.get("avatarUrl") or sender.get("avatar", ""),
            "senderName": sender.get("nickName") or sender.get("name", ""),
            "timestamp": int(time.time()),
            "isRead": False
        }
        
        self.messages[match_id].append(message)
        
        # 标记匹配为已读
        match = self.matches.get(match_id)
        if match:
            match["isRead"] = True
        
        return message
    
    def upload_file(self, file_type: str) -> dict[str, Any]:
        """上传文件"""
        # 模拟文件上传
        file_id = str(uuid.uuid4())
        return {
            "url": f"https://picsum.photos/400/300?random=upload-{file_type}-{file_id}"
        }

mock_data_service = MockDataService()
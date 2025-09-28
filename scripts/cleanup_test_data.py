#!/usr/bin/env python3
"""
高级测试数据清理脚本
用于清理数据库中的测试用卡片和用户数据
支持多种清理模式和精确识别
"""

import sys
import os
import re
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import argparse
from typing import List, Dict, Any, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestDataCleaner:
    """测试数据清理器"""
    
    def __init__(self, db_path: str, dry_run: bool = True):
        self.db_path = db_path
        self.dry_run = dry_run
        self.conn = None
        self.deleted_stats = {
            'cards': 0,
            'users': 0,
            'matches': 0,
            'chat_messages': 0
        }
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def is_test_data(self, text: str) -> bool:
        """判断文本是否包含测试相关关键词"""
        if not text:
            return False
        
        test_patterns = [
            r'测试', r'test', r'demo', r'示例', r'样例', r'mock',
            r'临时', r'temp', r'草稿', r'draft', r'实验', r'experiment'
        ]
        
        text_lower = text.lower()
        for pattern in test_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def is_test_user_id(self, user_id: str) -> bool:
        """判断用户ID是否为测试用户"""
        if not user_id:
            return False
        
        # 测试用户ID模式
        test_patterns = [
            r'test_', r'_test', r'demo_', r'_demo',
            r'user_test', r'test_user', r'12345', r'00000'
        ]
        
        for pattern in test_patterns:
            if re.search(pattern, user_id, re.IGNORECASE):
                return True
        
        return False
    
    def identify_test_cards(self, mode: str = 'conservative') -> List[Dict[str, Any]]:
        """识别测试卡片"""
        cursor = self.conn.cursor()
        
        # 基础查询条件
        base_conditions = []
        
        if mode == 'conservative':
            # 保守模式：只删除明显是测试的数据
            base_conditions = [
                "display_name LIKE '%测试%'",
                "LOWER(display_name) LIKE '%test%'",
                "bio LIKE '%测试%'",
                "LOWER(bio) LIKE '%test%'",
                "search_code LIKE '%test%'",
                "id LIKE 'card_test_%'"
            ]
        elif mode == 'aggressive':
            # 激进模式：删除更多可能的数据
            base_conditions = [
                "display_name LIKE '%测试%'",
                "LOWER(display_name) LIKE '%test%'",
                "LOWER(display_name) LIKE '%demo%'",
                "bio LIKE '%测试%'",
                "LOWER(bio) LIKE '%test%'",
                "LOWER(bio) LIKE '%demo%'",
                "search_code LIKE '%test%'",
                "search_code LIKE '%demo%'",
                "id LIKE 'card_test_%'",
                "id LIKE '%_test_%'",
                "user_id LIKE '%test%'",
                "user_id LIKE '%demo%'"
            ]
        elif mode == 'custom':
            # 自定义模式：基于时间或其他条件
            cutoff_date = datetime.now() - timedelta(days=30)  # 30天前的数据
            base_conditions = [
                f"created_at < '{cutoff_date.strftime('%Y-%m-%d')}'",
                "display_name LIKE '%测试%'",
                "LOWER(display_name) LIKE '%test%'"
            ]
        
        where_clause = " OR ".join(base_conditions)
        
        query = f"""
            SELECT 
                uc.id, uc.user_id, uc.display_name, uc.scene_type, uc.role_type,
                uc.bio, uc.search_code, uc.created_at, uc.is_active,
                u.nick_name as user_name, u.phone as user_phone
            FROM user_cards uc
            LEFT JOIN users u ON uc.user_id = u.id
            WHERE ({where_clause}) AND uc.is_deleted = 0
            ORDER BY uc.created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        test_cards = []
        for row in rows:
            card_data = dict(row)
            
            # 额外验证
            confidence_score = self.calculate_test_confidence(card_data)
            card_data['confidence_score'] = confidence_score
            
            if confidence_score >= 0.5:  # 置信度大于50%
                test_cards.append(card_data)
        
        return test_cards
    
    def calculate_test_confidence(self, card_data: Dict[str, Any]) -> float:
        """计算测试数据的置信度分数"""
        score = 0.0
        max_score = 0.0
        
        # 检查显示名称
        if card_data.get('display_name'):
            max_score += 1.0
            if self.is_test_data(card_data['display_name']):
                score += 1.0
        
        # 检查简介
        if card_data.get('bio'):
            max_score += 0.8
            if self.is_test_data(card_data['bio']):
                score += 0.8
        
        # 检查搜索代码
        if card_data.get('search_code'):
            max_score += 0.6
            if self.is_test_data(card_data['search_code']):
                score += 0.6
        
        # 检查用户名称
        if card_data.get('user_name'):
            max_score += 0.4
            if self.is_test_data(card_data['user_name']):
                score += 0.4
        
        # 检查用户ID
        if card_data.get('user_id'):
            max_score += 0.3
            if self.is_test_user_id(card_data['user_id']):
                score += 0.3
        
        # 检查卡片ID
        if card_data.get('id'):
            max_score += 0.3
            if 'test' in card_data['id'].lower():
                score += 0.3
        
        # 检查创建时间（很新的数据可能是测试数据）
        if card_data.get('created_at'):
            max_score += 0.2
            created_at = datetime.fromisoformat(card_data['created_at'])
            if datetime.now() - created_at < timedelta(hours=1):
                score += 0.2
        
        return score / max_score if max_score > 0 else 0.0
    
    def soft_delete_cards(self, card_ids: List[str]) -> int:
        """软删除卡片"""
        if not card_ids:
            return 0
        
        cursor = self.conn.cursor()
        
        placeholders = ",".join(["?" for _ in card_ids])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = f"""
            UPDATE user_cards 
            SET is_deleted = 1, updated_at = ? 
            WHERE id IN ({placeholders}) AND is_deleted = 0
        """
        
        cursor.execute(query, [current_time] + card_ids)
        deleted_count = cursor.rowcount
        
        if not self.dry_run:
            self.conn.commit()
        
        self.deleted_stats['cards'] += deleted_count
        return deleted_count
    
    def cleanup_related_data(self, card_ids: List[str]):
        """清理相关数据（匹配记录、聊天记录等）"""
        if not card_ids:
            return
        
        cursor = self.conn.cursor()
        placeholders = ",".join(["?" for _ in card_ids])
        
        # 清理匹配记录
        match_query = f"""
            UPDATE match_results 
            SET is_deleted = 1 
            WHERE card_id_1 IN ({placeholders}) OR card_id_2 IN ({placeholders})
        """
        cursor.execute(match_query, card_ids + card_ids)
        self.deleted_stats['matches'] += cursor.rowcount
        
        # 清理匹配动作
        action_query = f"""
            UPDATE match_actions 
            SET is_deleted = 1 
            WHERE card_id IN ({placeholders})
        """
        cursor.execute(action_query, card_ids)
        
        # 清理聊天记录
        chat_query = f"""
            UPDATE chat_messages 
            SET is_deleted = 1 
            WHERE card_id IN ({placeholders})
        """
        cursor.execute(chat_query, card_ids)
        self.deleted_stats['chat_messages'] += cursor.rowcount
        
        if not self.dry_run:
            self.conn.commit()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # 卡片统计
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 0")
        stats['active_cards'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1")
        stats['deleted_cards'] = cursor.fetchone()[0]
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_deleted = 0")
        stats['active_users'] = cursor.fetchone()[0]
        
        # 匹配统计
        cursor.execute("SELECT COUNT(*) FROM match_results WHERE is_deleted = 0")
        stats['active_matches'] = cursor.fetchone()[0]
        
        return stats
    
    def generate_cleanup_report(self, test_cards: List[Dict[str, Any]]) -> str:
        """生成清理报告"""
        report = []
        report.append("=== 测试数据清理报告 ===")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 数据库统计
        stats = self.get_database_stats()
        report.append("数据库统计:")
        report.append(f"  活跃卡片: {stats['active_cards']}")
        report.append(f"  已删除卡片: {stats['deleted_cards']}")
        report.append(f"  活跃用户: {stats['active_users']}")
        report.append(f"  活跃匹配: {stats['active_matches']}")
        report.append("")
        
        # 发现的测试卡片
        report.append(f"发现的测试卡片: {len(test_cards)}")
        
        if test_cards:
            report.append("\n测试卡片详情:")
            for i, card in enumerate(test_cards[:10]):  # 显示前10个
                report.append(f"  {i+1:2d}. {card['display_name']} ({card['id']})")
                report.append(f"      置信度: {card['confidence_score']:.1%}")
                report.append(f"      用户: {card['user_name']} ({card['user_id']})")
                report.append(f"      场景: {card['scene_type']}, 角色: {card['role_type']}")
                report.append(f"      创建时间: {card['created_at']}")
                
                if card.get('bio'):
                    bio_preview = card['bio'][:50] + '...' if len(card['bio']) > 50 else card['bio']
                    report.append(f"      简介: {bio_preview}")
                report.append("")
            
            if len(test_cards) > 10:
                report.append(f"  ... 还有 {len(test_cards) - 10} 个卡片未显示")
        
        # 删除统计
        if self.deleted_stats['cards'] > 0:
            report.append("\n删除统计:")
            report.append(f"  删除卡片: {self.deleted_stats['cards']}")
            report.append(f"  删除匹配: {self.deleted_stats['matches']}")
            report.append(f"  删除聊天记录: {self.deleted_stats['chat_messages']}")
        
        return "\n".join(report)

def get_db_path():
    """获取数据库路径"""
    # 检查环境变量
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and "sqlite" in db_url:
        # 从URL中提取路径
        db_path = db_url.replace("sqlite:///", "")
        # 处理相对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(Path(__file__).parent.parent, db_path)
        return db_path
    
    # 默认使用项目根目录下的数据库文件
    return os.path.join(Path(__file__).parent.parent, "vmatch_dev.db")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='清理数据库中的测试数据')
    parser.add_argument('--mode', choices=['conservative', 'aggressive', 'custom'], 
                       default='conservative', help='清理模式')
    parser.add_argument('--dry-run', action='store_true', 
                       help='只显示要删除的数据，不实际删除')
    parser.add_argument('--force', action='store_true', 
                       help='强制删除，不询问确认')
    parser.add_argument('--cleanup-related', action='store_true', 
                       help='同时清理相关的匹配和聊天记录')
    parser.add_argument('--output-report', type=str,
                       help='输出报告到指定文件')
    
    args = parser.parse_args()
    
    print("=== 测试数据清理工具 ===")
    
    # 获取数据库路径
    db_path = get_db_path()
    print(f"数据库路径: {db_path}")
    
    # 检查数据库文件
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return 1
    
    # 创建清理器
    cleaner = TestDataCleaner(db_path, dry_run=args.dry_run)
    
    # 连接数据库
    if not cleaner.connect():
        return 1
    
    try:
        # 识别测试卡片
        print(f"正在使用 {args.mode} 模式识别测试卡片...")
        test_cards = cleaner.identify_test_cards(args.mode)
        
        if not test_cards:
            print("未找到测试卡片数据")
            return 0
        
        print(f"找到 {len(test_cards)} 个测试卡片")
        
        # 显示部分信息
        print("\n前5个测试卡片:")
        for i, card in enumerate(test_cards[:5]):
            print(f"  {i+1}. {card['display_name']} (置信度: {card['confidence_score']:.1%})")
        
        if len(test_cards) > 5:
            print(f"  ... 还有 {len(test_cards) - 5} 个")
        
        # 确认删除
        if not args.force and not args.dry_run:
            response = input(f"\n是否删除这 {len(test_cards)} 个测试卡片? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("取消删除操作")
                return 0
        
        # 执行删除
        if not args.dry_run:
            print(f"\n正在删除 {len(test_cards)} 个测试卡片...")
            
            # 提取卡片ID
            card_ids = [card['id'] for card in test_cards]
            
            # 删除卡片
            deleted_count = cleaner.soft_delete_cards(card_ids)
            print(f"已删除 {deleted_count} 个卡片")
            
            # 清理相关数据
            if args.cleanup_related:
                print("正在清理相关数据...")
                cleaner.cleanup_related_data(card_ids)
        
        # 生成报告
        report = cleaner.generate_cleanup_report(test_cards)
        print("\n" + report)
        
        # 输出报告到文件
        if args.output_report:
            with open(args.output_report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n报告已保存到: {args.output_report}")
        
        return 0
        
    except Exception as e:
        print(f"发生错误: {e}")
        return 1
        
    finally:
        cleaner.close()

if __name__ == "__main__":
    sys.exit(main())
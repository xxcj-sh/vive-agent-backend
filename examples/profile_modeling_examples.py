"""
用户画像离线建模模块使用示例
展示如何使用人设真实性验证、内容合规性验证、用户画像分析更新等功能
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.profile_modeling_service import ProfileModelingService
from app.services.profile_modeling_scheduler import ProfileModelingScheduler
from app.dependencies import get_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_verify_profile_authenticity():
    """
    示例：验证用户人设真实性
    
    这个示例展示了如何使用ProfileModelingService来验证用户人设的真实性。
    系统会分析用户的头像、个人简介、行为模式等信息，生成真实性评分。
    """
    logger.info("=== 人设真实性验证示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建建模服务
        modeling_service = ProfileModelingService(db)
        
        # 用户ID（请替换为实际的用户ID）
        user_id = 1
        
        logger.info(f"开始验证用户 {user_id} 的人设真实性...")
        
        # 执行真实性验证
        result = await modeling_service.verify_profile_authenticity(user_id)
        
        if result["success"]:
            logger.info(f"验证成功！")
            logger.info(f"真实性评分: {result['authenticity_score']}/100")
            logger.info(f"分析结果: {result['analysis_result']}")
            logger.info(f"关键因素: {', '.join(result['key_factors'])}")
            logger.info(f"风险评估: {result['risk_assessment']}")
            logger.info(f"建议: {', '.join(result['recommendations'])}")
        else:
            logger.error(f"验证失败: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


async def example_verify_content_compliance():
    """
    示例：验证卡片内容合规性
    
    这个示例展示了如何使用ProfileModelingService来验证用户卡片的内容合规性。
    系统会检查卡片内容是否包含违规信息，如不当内容、敏感词汇等。
    """
    logger.info("=== 内容合规性验证示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建建模服务
        modeling_service = ProfileModelingService(db)
        
        # 卡片ID（请替换为实际的卡片ID）
        card_id = 1
        
        logger.info(f"开始验证卡片 {card_id} 的内容合规性...")
        
        # 执行合规性验证
        result = await modeling_service.verify_content_compliance(card_id)
        
        if result["success"]:
            compliance_status = "通过" if result["is_compliant"] else "拒绝"
            logger.info(f"验证成功！状态: {compliance_status}")
            logger.info(f"合规性评分: {result['compliance_score']}/100")
            
            if result["is_compliant"]:
                logger.info(f"建议: {', '.join(result['suggestions'])}")
                logger.info(f"分类: {', '.join(result['categories'])}")
            else:
                logger.warning(f"发现违规内容:")
                for violation in result["violations"]:
                    logger.warning(f"  - 类型: {violation['type']}")
                    logger.warning(f"  - 描述: {violation['description']}")
                    logger.warning(f"  - 严重程度: {violation['severity']}")
                    logger.warning(f"  - 位置: {violation['location']}")
                
                logger.info(f"改进建议: {', '.join(result['suggestions'])}")
        else:
            logger.error(f"验证失败: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


async def example_update_user_profile():
    """
    示例：更新用户画像分析
    
    这个示例展示了如何使用ProfileModelingService来更新用户画像。
    系统会基于用户的最新聊天记录和新增卡片内容，推测用户的偏好、个性特征和心情状态。
    """
    logger.info("=== 用户画像更新示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建建模服务
        modeling_service = ProfileModelingService(db)
        
        # 用户ID（请替换为实际的用户ID）
        user_id = 1
        
        logger.info(f"开始更新用户 {user_id} 的画像分析...")
        
        # 执行画像更新（包含聊天记录和新卡片）
        result = await modeling_service.update_user_profile_analysis(
            user_id,
            include_recent_chats=True,
            include_new_cards=True
        )
        
        if result["success"]:
            logger.info(f"更新成功！")
            logger.info(f"置信度评分: {result['confidence_score']}/100")
            logger.info(f"分析摘要: {result['analysis_summary']}")
            
            logger.info(f"更新的字段:")
            if "preferences" in result["updated_fields"]:
                logger.info(f"  - 偏好: {result['updated_fields']['preferences']}")
            if "personality_traits" in result["updated_fields"]:
                logger.info(f"  - 个性特征: {result['updated_fields']['personality_traits']}")
            if "mood_status" in result["updated_fields"]:
                logger.info(f"  - 心情状态: {result['updated_fields']['mood_status']}")
            
            logger.info(f"关键洞察: {', '.join(result['key_insights'])}")
            logger.info(f"建议: {', '.join(result['recommendations'])}")
        else:
            logger.error(f"更新失败: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"更新过程中发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


async def example_scheduler_operations():
    """
    示例：调度器操作
    
    这个示例展示了如何使用ProfileModelingScheduler来管理离线任务。
    包括启动调度器、查看状态、更新配置等操作。
    """
    logger.info("=== 调度器操作示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建调度器
        scheduler = ProfileModelingScheduler(db)
        
        logger.info("1. 启动调度器...")
        scheduler.start()
        logger.info("调度器已启动")
        
        # 获取调度器状态
        logger.info("2. 获取调度器状态...")
        status = scheduler.get_task_status()
        logger.info(f"调度器运行状态: {status['scheduler_running']}")
        logger.info(f"任务数量: {len(status['jobs'])}")
        
        for job_id, job_info in status['jobs'].items():
            logger.info(f"  - 任务: {job_info['name']}")
            logger.info(f"    下次运行时间: {job_info['next_run_time']}")
        
        # 更新任务配置
        logger.info("3. 更新任务配置...")
        new_config = {
            "interval_hours": 48,  # 改为每48小时执行一次
            "batch_size": 25       # 每批处理25个用户
        }
        scheduler.update_task_config("authenticity_verification", new_config)
        logger.info("人设真实性验证任务配置已更新")
        
        # 显示更新后的配置
        updated_status = scheduler.get_task_status()
        logger.info(f"更新后的配置: {updated_status['task_configs']['authenticity_verification']}")
        
        # 注意：在实际应用中，调度器会持续运行
        # 这里只是演示基本操作，不会实际停止调度器
        logger.info("4. 调度器操作演示完成")
        
        return status
        
    except Exception as e:
        logger.error(f"调度器操作过程中发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


async def example_batch_operations():
    """
    示例：批量操作
    
    这个示例展示了如何批量处理多个用户或卡片的验证任务。
    """
    logger.info("=== 批量操作示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        modeling_service = ProfileModelingService(db)
        
        # 用户ID列表（请替换为实际的用户ID）
        user_ids = [1, 2, 3, 4, 5]
        
        logger.info(f"开始对 {len(user_ids)} 个用户进行人设真实性验证...")
        
        results = []
        for user_id in user_ids:
            try:
                result = await modeling_service.verify_profile_authenticity(user_id)
                results.append({
                    "user_id": user_id,
                    "success": result["success"],
                    "score": result.get("authenticity_score", 0),
                    "status": "完成" if result["success"] else "失败"
                })
                
                if result["success"]:
                    logger.info(f"用户 {user_id}: 评分 {result['authenticity_score']}/100")
                else:
                    logger.error(f"用户 {user_id}: 验证失败 - {result.get('error', '未知错误')}")
                
                # 添加延迟避免API调用过于频繁
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"用户 {user_id} 验证异常: {str(e)}")
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "score": 0,
                    "status": "异常"
                })
        
        # 统计结果
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        avg_score = sum(r["score"] for r in results if r["success"]) / successful if successful > 0 else 0
        
        logger.info(f"批量验证完成:")
        logger.info(f"  - 成功: {successful}")
        logger.info(f"  - 失败: {failed}")
        logger.info(f"  - 平均评分: {avg_score:.1f}/100")
        
        return results
        
    except Exception as e:
        logger.error(f"批量操作过程中发生错误: {str(e)}")
        return []
    
    finally:
        db.close()


async def example_error_handling():
    """
    示例：错误处理和重试机制
    
    这个示例展示了如何处理API调用失败的情况，并实现简单的重试机制。
    """
    logger.info("=== 错误处理和重试示例 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        modeling_service = ProfileModelingService(db)
        
        user_id = 1
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            logger.info(f"尝试 {attempt + 1}/{max_retries}: 验证用户 {user_id} 的人设真实性...")
            
            try:
                result = await modeling_service.verify_profile_authenticity(user_id)
                
                if result["success"]:
                    logger.info(f"验证成功！评分: {result['authenticity_score']}/100")
                    return result
                else:
                    logger.warning(f"验证失败: {result.get('error', '未知错误')}")
                    
                    # 如果是可重试的错误，继续尝试
                    if attempt < max_retries - 1:
                        logger.info(f"等待 {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error("所有重试尝试都失败了")
                        return result
                        
            except Exception as e:
                logger.error(f"验证异常: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error("所有重试尝试都失败了")
                    return {"success": False, "error": str(e)}
        
    except Exception as e:
        logger.error(f"示例执行过程中发生错误: {str(e)}")
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


async def main():
    """
    主函数：运行所有示例
    """
    logger.info("开始运行用户画像离线建模模块示例")
    logger.info("=" * 50)
    
    # 运行各个示例
    # await example_verify_profile_authenticity()
    # await asyncio.sleep(1)
    
    # await example_verify_content_compliance()
    # await asyncio.sleep(1)
    
    # await example_update_user_profile()
    # await asyncio.sleep(1)
    
    # await example_scheduler_operations()
    # await asyncio.sleep(1)
    
    # await example_batch_operations()
    # await asyncio.sleep(1)
    
    await example_error_handling()
    
    logger.info("所有示例运行完成")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())
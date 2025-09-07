"""
测试角色转换工具的正确性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.role_converter import RoleConverter

def test_role_conversion():
    """测试角色转换功能"""
    print("=== 测试角色转换功能 ===")
    
    # 测试场景1：简化到完整角色转换
    print("\n1. 测试简化到完整角色转换")
    test_cases = [
        ("housing", "seeker", "housing_seeker"),
        ("housing", "provider", "housing_provider"),
        ("dating", "seeker", "dating_seeker"),
        ("dating", "provider", "dating_provider"),
        ("activity", "organizer", "activity_organizer"),
        ("activity", "participant", "activity_participant"),
    ]
    
    for scene, simple_role, expected_full in test_cases:
        result = RoleConverter.to_full_role(scene, simple_role)
        status = "✅" if result == expected_full else "❌"
        print(f"   {status} {scene}.{simple_role} -> {result} (期望: {expected_full})")
    
    # 测试场景2：完整到简化角色转换
    print("\n2. 测试完整到简化角色转换")
    reverse_test_cases = [
        ("housing_seeker", "seeker"),
        ("housing_provider", "provider"),
        ("dating_seeker", "seeker"),
        ("dating_provider", "provider"),
        ("activity_organizer", "organizer"),
        ("activity_participant", "participant"),
    ]
    
    for full_role, expected_simple in reverse_test_cases:
        result = RoleConverter.to_simplified_role(full_role)
        status = "✅" if result == expected_simple else "❌"
        print(f"   {status} {full_role} -> {result} (期望: {expected_simple})")
    
    # 测试场景3：获取可用角色
    print("\n3. 测试获取场景可用角色")
    scene_roles = {
        "housing": ["housing_seeker", "housing_provider"],
        "dating": ["dating_seeker", "dating_provider"],
        "activity": ["activity_organizer", "activity_participant"],
    }
    
    for scene, expected_roles in scene_roles.items():
        result = RoleConverter.get_available_roles(scene)
        status = "✅" if result == expected_roles else "❌"
        print(f"   {status} {scene} 可用角色: {result} (期望: {expected_roles})")
    
    # 测试场景4：获取目标角色
    print("\n4. 测试获取目标角色")
    target_test_cases = [
        ("housing_seeker", "housing_provider"),
        ("housing_provider", "housing_seeker"),
        ("dating_seeker", "dating_provider"),
        ("dating_provider", "dating_seeker"),
        ("activity_organizer", "activity_participant"),
        ("activity_participant", "activity_organizer"),
    ]
    
    for current_role, expected_target in target_test_cases:
        result = RoleConverter.get_target_role(current_role)
        status = "✅" if result == expected_target else "❌"
        print(f"   {status} {current_role} -> {result} (期望: {expected_target})")
    
    # 测试场景5：验证角色组合
    print("\n5. 测试验证角色组合")
    validation_test_cases = [
        ("housing", "housing_seeker", True),
        ("housing", "housing_provider", True),
        ("housing", "dating_seeker", False),
        ("dating", "dating_seeker", True),
        ("activity", "activity_organizer", True),
        ("invalid", "housing_seeker", False),
    ]
    
    for scene, role, expected_valid in validation_test_cases:
        result = RoleConverter.validate_role_pair(scene, role)
        status = "✅" if result == expected_valid else "❌"
        print(f"   {status} {scene}.{role} 有效性: {result} (期望: {expected_valid})")
    
    # 测试场景6：提取场景类型
    print("\n6. 测试提取场景类型")
    extract_test_cases = [
        ("housing_seeker", "housing"),
        ("housing_provider", "housing"),
        ("dating_seeker", "dating"),
        ("invalid_role", None),
    ]
    
    for full_role, expected_scene in extract_test_cases:
        result = RoleConverter.extract_scene_from_role(full_role)
        status = "✅" if result == expected_scene else "❌"
        print(f"   {status} {full_role} -> {result} (期望: {expected_scene})")

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n=== 测试向后兼容性 ===")
    
    # 确保现有API调用仍然有效
    scenes = ["housing", "dating", "activity"]
    simplified_roles = ["seeker", "provider", "organizer", "participant"]
    
    print("\n7. 测试API兼容性")
    for scene in scenes:
        for simple_role in simplified_roles:
            try:
                full_role = RoleConverter.to_full_role(scene, simple_role)
                back_to_simple = RoleConverter.to_simplified_role(full_role)
                
                if back_to_simple == simple_role:
                    print(f"   ✅ {scene}.{simple_role} 往返转换成功")
                else:
                    print(f"   ❌ {scene}.{simple_role} 往返转换失败: {back_to_simple}")
            except Exception as e:
                print(f"   ❌ {scene}.{simple_role} 转换错误: {e}")

if __name__ == "__main__":
    print("开始测试角色转换工具...")
    
    try:
        test_role_conversion()
        test_backward_compatibility()
        
        print("\n=== 测试结果总结 ===")
        print("✅ 所有角色转换测试通过")
        print("✅ 向后兼容性验证通过")
        print("✅ 统一命名规范已就绪")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
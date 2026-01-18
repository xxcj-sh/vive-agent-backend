from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from app.models import UserConnection, ConnectionStatus, ConnectionType
from app.models.user import User
from app.models.user_connection import UserConnectionCreate, UserConnectionUpdate
from datetime import datetime, timedelta

class UserConnectionService:
    """用户连接服务类，处理用户之间的人脉关系管理"""
    
    @staticmethod
    def record_visit(db: Session, from_user_id: str, to_user_id: str) -> UserConnection:
        """
        记录用户访问行为（访问他人主页）
        
        Args:
            db: 数据库会话
            from_user_id: 访问者的用户ID
            to_user_id: 被访问者的用户ID
            
        Returns:
            创建或更新的连接对象
        """
        # 检查是否是自己访问自己
        if from_user_id == to_user_id:
            return None
        
        # 查找是否已存在VISIT类型的连接
        existing_connection = db.query(UserConnection).filter(
            UserConnection.from_user_id == from_user_id,
            UserConnection.to_user_id == to_user_id,
            UserConnection.connection_type == ConnectionType.VISIT
        ).first()
        
        if existing_connection:
            # 更新访问时间
            existing_connection.updated_at = func.now()
            db.commit()
            db.refresh(existing_connection)
            return existing_connection
        else:
            # 创建新的访问记录
            db_connection = UserConnection(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                connection_type=ConnectionType.VISIT,
                status=ConnectionStatus.ACCEPTED
            )
            db.add(db_connection)
            db.commit()
            db.refresh(db_connection)
            return db_connection
    
    @staticmethod
    def get_recommended_users(db: Session, current_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取推荐用户列表
        
        推荐逻辑：
        1. 根据用户上次访问(VISIT)时间顺序排列，选取最久未访问的若干用户
        2. 从中剔除最近两周曾经浏览(VIEW)过的用户
        3. 按顺序展示给用户
        
        Args:
            db: 数据库会话
            current_user_id: 当前用户ID
            limit: 返回用户数量限制
            
        Returns:
            推荐用户列表，包含用户信息和连接信息
        """
        # 获取最近两周的时间
        two_weeks_ago = datetime.now() - timedelta(weeks=2)
        
        # 获取最近两周浏览过的用户ID列表（VIEW类型）
        recent_viewed_user_ids = db.query(UserConnection.to_user_id).filter(
            UserConnection.from_user_id == current_user_id,
            UserConnection.connection_type == ConnectionType.VIEW,
            UserConnection.updated_at >= two_weeks_ago
        ).distinct().all()
        
        # 提取用户ID
        excluded_user_ids = [user_id[0] for user_id in recent_viewed_user_ids]
        excluded_user_ids = []

        # 获取所有访问过的用户，按访问时间升序排列（最久未访问的在前）
        visited_connections = db.query(UserConnection).filter(
            UserConnection.from_user_id == current_user_id,
            UserConnection.connection_type == ConnectionType.VISIT
        ).order_by(UserConnection.updated_at.asc()).all()
        
        # 提取访问过的用户ID
        visited_user_ids = [conn.to_user_id for conn in visited_connections]
        
        # 获取最近两周访问过当前用户主页的用户（这些用户应该被优先推荐）
        recent_visitors = db.query(UserConnection).filter(
            UserConnection.to_user_id == current_user_id,
            UserConnection.connection_type == ConnectionType.VISIT,
            UserConnection.updated_at >= two_weeks_ago
        ).order_by(UserConnection.updated_at.desc()).all()
        
        # 提取最近访客的用户ID
        recent_visitor_ids = [conn.from_user_id for conn in recent_visitors]
        
        # 如果没有访问记录，获取所有活跃用户（排除自己和已注销用户）
        if not visited_user_ids:
            candidate_users = db.query(User).filter(
                and_(
                    User.id != current_user_id,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).limit(limit * 2).all()
        else:
            # 获取访问过的用户，按访问时间排序，只包含活跃用户
            candidate_users = db.query(User).filter(
                and_(
                    User.id.in_(visited_user_ids),
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).all()
            
            # 按访问时间排序（最久未访问的在前）
            user_visit_map = {conn.to_user_id: conn.updated_at for conn in visited_connections}
            candidate_users.sort(key=lambda user: user_visit_map.get(user.id, datetime.min))
        
        # 过滤掉最近两周浏览过的用户
        filtered_users = [user for user in candidate_users if user.id not in excluded_user_ids]
        
        # 合并最近访客到推荐列表（优先展示）
        # 1. 首先获取最近访客的用户对象，只包含活跃用户
        if recent_visitor_ids:
            recent_visitor_users = db.query(User).filter(
                and_(
                    User.id.in_(recent_visitor_ids),
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).all()
            
            # 按访问时间排序（最近的在前）
            visitor_time_map = {conn.from_user_id: conn.updated_at for conn in recent_visitors}
            recent_visitor_users.sort(key=lambda user: visitor_time_map.get(user.id, datetime.min), reverse=True)
            
            # 2. 将最近访客添加到推荐列表前面，并去重
            final_recommended = []
            added_user_ids = set()
            
            # 首先添加最近访客
            for user in recent_visitor_users:
                if user.id not in added_user_ids and user.id != current_user_id:
                    final_recommended.append(user)
                    added_user_ids.add(user.id)
            
            # 然后添加其他推荐用户
            for user in filtered_users:
                if user.id not in added_user_ids:
                    final_recommended.append(user)
                    added_user_ids.add(user.id)
                    if len(final_recommended) >= limit:
                        break
            
            recommended_users = final_recommended[:limit]
        else:
            # 如果没有最近访客，使用原有的推荐逻辑
            recommended_users = filtered_users[:limit]
        
        # 构建返回数据
        result = []
        for user in recommended_users:
            # 获取该用户的访问记录
            visit_record = next((conn for conn in visited_connections if conn.to_user_id == user.id), None)
            
            user_data = {
                "id": user.id,
                "nick_name": user.nick_name,
                "avatar_url": user.avatar_url,
                "gender": user.gender,
                "age": user.age,
                "occupation": user.occupation,
                "location": user.location,
                "bio": user.bio,
                "last_visit_time": visit_record.updated_at if visit_record else None,
                "connection_info": {
                    "has_visited": visit_record is not None,
                    "visit_count": len([conn for conn in visited_connections if conn.to_user_id == user.id])
                }
            }
            result.append(user_data)
        
        return result
    
    @staticmethod
    def record_view(db: Session, from_user_id: str, to_user_id: str) -> UserConnection:
        """
        记录用户浏览行为（在Index页面浏览用户卡片）
        
        Args:
            db: 数据库会话
            from_user_id: 浏览者的用户ID
            to_user_id: 被浏览者的用户ID
            
        Returns:
            创建或更新的连接对象
        """
        # 检查是否是自己浏览自己
        if from_user_id == to_user_id:
            return None
        
        # 查找是否已存在VIEW类型的连接
        existing_connection = db.query(UserConnection).filter(
            UserConnection.from_user_id == from_user_id,
            UserConnection.to_user_id == to_user_id,
            UserConnection.connection_type == ConnectionType.VIEW
        ).first()
        
        if existing_connection:
            # 更新浏览时间
            existing_connection.updated_at = func.now()
            db.commit()
            db.refresh(existing_connection)
            return existing_connection
        else:
            # 创建新的浏览记录
            db_connection = UserConnection(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                connection_type=ConnectionType.VIEW,  # 使用VIEW类型
                status=ConnectionStatus.ACCEPTED  # 关系直接接受
            )
            db.add(db_connection)
            db.commit()
            db.refresh(db_connection)
            return db_connection
    
    @staticmethod
    def create_connection(db: Session, from_user_id: str, connection_data: UserConnectionCreate) -> UserConnection:
        """
        创建用户连接请求
        
        Args:
            db: 数据库会话
            from_user_id: 请求发起者的用户ID
            connection_data: 连接请求数据
            
        Returns:
            创建的连接对象
            
        Raises:
            HTTPException: 当请求无效时抛出异常
        """
        # 检查是否是自己加自己
        if from_user_id == connection_data.to_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能与自己建立连接"
            )
        
        # 检查是否已经存在相同的连接请求
        existing_connection = db.query(UserConnection).filter(
            or_(
                and_(
                    UserConnection.from_user_id == from_user_id,
                    UserConnection.to_user_id == connection_data.to_user_id
                ),
                and_(
                    UserConnection.from_user_id == connection_data.to_user_id,
                    UserConnection.to_user_id == from_user_id
                )
            )
        ).first()
        
        if existing_connection:
            return existing_connection
        
        # 检查目标用户是否存在
        target_user = db.query(User).filter(User.id == connection_data.to_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标用户不存在"
            )
        
        # 创建新的连接请求
        db_connection = UserConnection(
            from_user_id=from_user_id,
            to_user_id=connection_data.to_user_id,
            connection_type=connection_data.connection_type,
            status=ConnectionStatus.PENDING,
            remark=connection_data.remark
        )
        
        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)
        
        return db_connection
    
    @staticmethod
    def update_connection_status(db: Session, connection_id: str, user_id: str, 
                                update_data: UserConnectionUpdate) -> UserConnection:
        """
        更新连接状态（接受/拒绝/拉黑）
        
        Args:
            db: 数据库会话
            connection_id: 连接ID
            user_id: 当前操作用户ID
            update_data: 更新数据
            
        Returns:
            更新后的连接对象
            
        Raises:
            HTTPException: 当连接不存在或用户无权操作时抛出异常
        """
        # 查找连接记录
        connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="连接记录不存在"
            )
        
        # 检查用户是否有权限操作（只有被请求方可以接受/拒绝）
        if connection.to_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此连接请求"
            )
        
        # 如果已经不是待处理状态，不允许再次更新
        if connection.status != ConnectionStatus.PENDING and update_data.status in [ConnectionStatus.ACCEPTED, ConnectionStatus.REJECTED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该连接请求已经处理过"
            )
        
        # 更新状态
        connection.status = update_data.status
        if update_data.remark:
            connection.remark = update_data.remark
        
        db.commit()
        db.refresh(connection)
        
        return connection
    
    @staticmethod
    def get_user_connections(db: Session, user_id: str, 
                             connection_type: Optional[ConnectionType] = None,
                             status: Optional[ConnectionStatus] = None,
                             as_requester: bool = True, as_addressee: bool = True) -> List[UserConnection]:
        """
        获取用户的连接列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            connection_type: 连接类型过滤
            status: 状态过滤
            as_requester: 是否包含作为发起者的连接
            as_addressee: 是否包含作为接收者的连接
            
        Returns:
            连接对象列表
        """
        query = db.query(UserConnection)
        
        # 构建查询条件
        conditions = []
        if as_requester:
            conditions.append(UserConnection.from_user_id == user_id)
        if as_addressee:
            conditions.append(UserConnection.to_user_id == user_id)
        
        if conditions:
            query = query.filter(or_(*conditions))
        else:
            return []
        
        # 类型过滤
        if connection_type:
            query = query.filter(UserConnection.connection_type == connection_type)
        
        # 状态过滤
        if status:
            query = query.filter(UserConnection.status == status)
        
        # 按创建时间倒序排列
        query = query.order_by(UserConnection.created_at.desc())
        
        # 加载关联的用户信息
        query = query.options(
            joinedload(UserConnection.from_user),
            joinedload(UserConnection.to_user)
        )
        
        return query.all()
    
    @staticmethod
    def get_connection_with_user_info(db: Session, connection: UserConnection, current_user_id: str) -> Dict[str, Any]:
        """
        获取连接信息，并包含对方用户的基本信息
        
        Args:
            db: 数据库会话
            connection: 连接对象
            current_user_id: 当前用户ID
            
        Returns:
            包含用户信息的连接数据
        """
        # 判断对方是请求方还是接收方
        if current_user_id == connection.from_user_id:
            target_user = connection.to_user
        else:
            target_user = connection.from_user
        
        # 构建返回数据
        result = {
            "id": connection.id,
            "from_user_id": connection.from_user_id,
            "to_user_id": connection.to_user_id,
            "connection_type": connection.connection_type,
            "status": connection.status,
            "remark": connection.remark,
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
            "target_user": {
                "id": target_user.id,
                "nick_name": target_user.nick_name,
                "avatar_url": target_user.avatar_url,
                "gender": target_user.gender,
                "age": target_user.age,
                "occupation": target_user.occupation,
                "location": target_user.location,
                "bio": target_user.bio
            }
        }
        
        return result
    
    @staticmethod
    def delete_connection(db: Session, connection_id: str, user_id: str) -> bool:
        """
        删除连接关系
        
        Args:
            db: 数据库会话
            connection_id: 连接ID
            user_id: 当前操作用户ID
            
        Returns:
            是否删除成功
            
        Raises:
            HTTPException: 当连接不存在或用户无权操作时抛出异常
        """
        # 查找连接记录
        connection = db.query(UserConnection).filter(UserConnection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="连接记录不存在"
            )
        
        # 检查用户是否有权限操作（只有连接的双方可以删除）
        if connection.from_user_id != user_id and connection.to_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此连接"
            )
        
        db.delete(connection)
        db.commit()
        
        return True
    
    @staticmethod
    def check_connection(db: Session, user_id: str, target_user_id: str) -> Optional[UserConnection]:
        """
        检查两个用户之间是否存在连接关系
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            target_user_id: 目标用户ID
            
        Returns:
            如果存在连接关系，返回连接对象；否则返回None
        """
        return db.query(UserConnection).filter(
            or_(
                and_(
                    UserConnection.from_user_id == user_id,
                    UserConnection.to_user_id == target_user_id
                ),
                and_(
                    UserConnection.from_user_id == target_user_id,
                    UserConnection.to_user_id == user_id
                )
            )
        ).first()
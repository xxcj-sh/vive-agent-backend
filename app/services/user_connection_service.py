from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models import UserConnection, ConnectionStatus, ConnectionType, User
from app.models.user_connection import UserConnectionCreate, UserConnectionUpdate

class UserConnectionService:
    """用户连接服务类，处理用户之间的人脉关系管理"""
    
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
            # 如果已有待处理请求，直接返回
            if existing_connection.status == ConnectionStatus.PENDING:
                return existing_connection
            # 如果已有接受的连接，提示已存在
            elif existing_connection.status == ConnectionStatus.ACCEPTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="已存在与该用户的连接关系"
                )
        
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

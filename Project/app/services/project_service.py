"""项目服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self, zone: str = None, category: str = None,
        suitable_age: str = None, status: str = "open",
    ) -> list[Project]:
        q = select(Project)
        if zone:
            q = q.where(Project.zone == zone)
        if category:
            q = q.where(Project.category == category)
        if status:
            q = q.where(Project.status == status)
        q = q.order_by(Project.sort_order)
        result = await self.db.execute(q)
        projects = list(result.scalars().all())

        if suitable_age:
            projects = self._filter_by_age(projects, suitable_age)

        return projects

    def _filter_by_age(self, projects: list, age: str) -> list[Project]:
        """按年龄筛选项目"""
        age_num = int(''.join(filter(str.isdigit, age))) if any(c.isdigit() for c in age) else 0
        filtered = []
        for p in projects:
            sa = p.suitable_age or ""
            if "全年龄" in sa:
                filtered.append(p)
            elif age_num > 0:
                import re
                m = re.findall(r'(\d+)', sa)
                if len(m) == 2 and int(m[0]) <= age_num <= int(m[1]):
                    filtered.append(p)
                elif len(m) == 1 and "以上" in sa and age_num >= int(m[0]):
                    filtered.append(p)
                elif len(m) == 1 and "-" in sa and int(m[0]) <= age_num:
                    filtered.append(p)
        return filtered or projects

    async def get_project(self, project_id: int) -> Project | None:
        return await self.db.get(Project, project_id)

    async def get_project_by_code(self, code: str) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.project_code == code))
        return result.scalar_one_or_none()

    async def recommend(self, age: str = None, interests: str = None, indoor: bool = None) -> list[Project]:
        q = select(Project).where(Project.status == "open")
        if indoor:
            q = q.where(Project.is_indoor == True)
        q = q.order_by(Project.sort_order)
        result = await self.db.execute(q)
        projects = list(result.scalars().all())

        if age:
            # 简单过滤：按 suitable_age 匹配
            age_num = int(''.join(filter(str.isdigit, age))) if any(c.isdigit() for c in age) else 0
            filtered = []
            for p in projects:
                sa = p.suitable_age or ""
                if "全年龄" in sa:
                    filtered.append(p)
                elif age_num > 0:
                    # 解析 "0-3岁" "3-6岁" "6-12岁" "3岁以上"
                    import re
                    m = re.findall(r'(\d+)', sa)
                    if len(m) == 2 and int(m[0]) <= age_num <= int(m[1]):
                        filtered.append(p)
                    elif len(m) == 1 and "以上" in sa and age_num >= int(m[0]):
                        filtered.append(p)
                    elif len(m) == 1 and "-" in sa and int(m[0]) <= age_num:
                        filtered.append(p)
            if filtered:
                projects = filtered

        return projects

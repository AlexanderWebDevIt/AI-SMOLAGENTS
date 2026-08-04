from typing import List, Dict, Any
from datetime import datetime
import json


class Task:
    def __init__(self, id: str, description: str, status: str = 'pending', parent_id: str = None):
        self.id = id
        self.description = description
        self.status = status  # pending, in_progress, completed, failed
        self.parent_id = parent_id
        self.steps = []
        now = datetime.now().isoformat()
        self.created_at = now
        self.updated_at = now


class Planner:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, description: str, parent_id: str = None) -> Task:
        '''Create a new task with auto-generated ID'''
        import uuid
        task_id = str(uuid.uuid4())
        task = Task(task_id, description, 'pending', parent_id)
        self.tasks[task_id] = task
        return task
    
    def update_task(self, task_id: str, status: str = None, steps: List[str] = None) -> bool:
        '''Update task status and/or steps'''
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if status:
            task.status = status
        if steps:
            task.steps.extend(steps)
        task.updated_at = datetime.now().isoformat()
        
        return True
    
    def decompose_task(self, task_description: str) -> List[str]:
        '''Decompose a complex task into smaller steps'''
        if 'analyze' in task_description.lower() or 'review' in task_description.lower():
            return ['Identify key components', 'Gather relevant data', 'Analyze each component', 'Draw conclusions', 'Document findings']
        elif 'create' in task_description.lower() or 'build' in task_description.lower():
            return ['Define requirements', 'Design solution architecture', 'Implement components', 'Test functionality', 'Document and deploy']
        elif 'calculate' in task_description.lower() or 'compute' in task_description.lower():
            return ['Identify input data', 'Write calculation logic', 'Execute computation', 'Verify results', 'Report findings']
        else:
            return ['Break down the task into smaller steps', 'Execute each step', 'Review results']
    
    def get_task(self, task_id: str) -> Task:
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[Task]:
        return list(self.tasks.values())
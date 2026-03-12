import os

directories = [
    "app/api",
    "app/core",
    "app/domains/auth",
    "app/domains/users",
    "app/domains/chat",
    "app/domains/courses",
    "app/domains/transport",
    "app/domains/tasks",
    "app/domains/schedule",
    "app/domains/grades",
    "app/shared",
    "app/templates",
    "tests",
    "alembic"
]

files = [
    "app/main.py",
    "app/api/router.py",
    "app/core/config.py", "app/core/database.py", "app/core/security.py", "app/core/dependencies.py", "app/core/logging.py",
  
    "app/domains/auth/router.py", "app/domains/auth/schemas.py", "app/domains/auth/service.py", "app/domains/auth/dependencies.py",
    
    "app/domains/users/router.py", "app/domains/users/schemas.py", "app/domains/users/models.py", "app/domains/users/service.py", "app/domains/users/repository.py",
  
    "app/domains/chat/router.py", "app/domains/chat/websocket.py", "app/domains/chat/schemas.py", "app/domains/chat/models.py", "app/domains/chat/service.py", 
    
    "app/domains/courses/router.py", "app/domains/courses/schemas.py", "app/domains/courses/models.py", "app/domains/courses/service.py", "app/domains/courses/repository.py",
    
    "app/domains/transport/router.py", "app/domains/transport/schemas.py", "app/domains/transport/models.py", "app/domains/transport/service.py",
    
    "app/domains/tasks/router.py", "app/domains/tasks/schemas.py", "app/domains/tasks/models.py", "app/domains/tasks/service.py",
    
    "app/domains/schedule/router.py", "app/domains/schedule/schemas.py", "app/domains/schedule/models.py", "app/domains/schedule/service.py",
    "app/domains/grades/router.py", "app/domains/grades/schemas.py", "app/domains/grades/models.py", "app/domains/grades/service.py",

    "app/shared/exceptions.py", "app/shared/utils.py",
    "requirements.txt",
    ".env",
    ".env.example"
    ".gitignore"
]

for d in directories:
    os.makedirs(d, exist_ok=True)

    init_file = os.path.join(d, "__init__.py")
    with open(init_file, 'w') as f:
        pass

with open("app/__init__.py", 'w') as f: pass
with open("app/domains/__init__.py", 'w') as f: pass

for f in files:
    with open(f, 'w') as file:
        pass
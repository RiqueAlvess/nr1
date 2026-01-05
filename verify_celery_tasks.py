#!/usr/bin/env python
"""
Script para verificar tasks registradas no Celery
Executar: python verify_celery_tasks.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nr1_platform.settings')
django.setup()

from nr1_platform.celery import app

print("=" * 80)
print("TASKS REGISTRADAS NO CELERY")
print("=" * 80)

# Listar todas as tasks (exceto as do celery interno)
tasks = sorted([k for k in app.tasks.keys() if not k.startswith('celery.')])

print(f"\nTotal de tasks: {len(tasks)}\n")

# Destacar tasks relacionadas a email, usercompany e quiz
relevant_keywords = ['email', 'usercompany', 'quiz']
relevant_tasks = []
other_tasks = []

for task in tasks:
    if any(keyword in task.lower() for keyword in relevant_keywords):
        relevant_tasks.append(task)
    else:
        other_tasks.append(task)

if relevant_tasks:
    print("Tasks relevantes (email, usercompany, quiz):")
    print("-" * 80)
    for task in relevant_tasks:
        print(f"  ✓ {task}")

if other_tasks:
    print("\nOutras tasks:")
    print("-" * 80)
    for task in other_tasks:
        print(f"  • {task}")

print("\n" + "=" * 80)
print("VERIFICAÇÃO CONCLUÍDA")
print("=" * 80)

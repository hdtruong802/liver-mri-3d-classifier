"""Giải thích dự đoán: Grad-CAM 3D và độ nhạy theo thì.

Mọi thứ ở đây chạy **offline** (Kaggle), không phải trong web app: backend bị ràng
buộc không kéo theo torch (AGENTS.md §4), mà Grad-CAM thì cần backward pass.
"""

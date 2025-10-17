"""Test script to verify the setup"""
import sys
sys.path.insert(0, '/home/engine/project')

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        # Backend imports
        from backend.app import main, config, database
        from backend.app.models import User, DataSet, DataRecord, ActivityLog
        from backend.app.schemas import user, dataset, record, analytics
        from backend.app.api import auth, users, datasets, records, analytics as analytics_api
        from backend.app.core import security, deps, middleware
        from backend.app.services import nlp_service, analytics_service
        print("✅ All backend modules imported successfully")
        
        # Check FastAPI app
        app = main.app
        print(f"✅ FastAPI app created: {app.title}")
        
        # Check database
        from backend.app.database import engine, init_db
        init_db()
        print("✅ Database initialized")
        
        # Check settings
        settings = config.get_settings()
        print(f"✅ Settings loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test if models work correctly"""
    print("\nTesting models...")
    
    try:
        from backend.app.database import SessionLocal
        from backend.app.models import User
        from backend.app.models.user import UserRole
        from backend.app.core.security import get_password_hash
        
        db = SessionLocal()
        
        # Check if we can query users
        users = db.query(User).all()
        print(f"✅ Found {len(users)} users in database")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_security():
    """Test security functions"""
    print("\nTesting security...")
    
    try:
        from backend.app.core.security import get_password_hash, verify_password, create_access_token
        
        # Test password hashing
        password = "test123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed), "Password verification failed"
        print("✅ Password hashing works")
        
        # Test JWT
        token = create_access_token(1)
        assert token, "Token creation failed"
        print("✅ JWT token creation works")
        
        return True
    except Exception as e:
        print(f"❌ Security error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nlp():
    """Test NLP service"""
    print("\nTesting NLP...")
    
    try:
        from backend.app.services.nlp_service import NLPService
        
        # Test sentiment analysis
        text = "这个产品非常好，我很喜欢！"
        score, label = NLPService.analyze_sentiment(text)
        print(f"✅ Sentiment analysis works: '{text}' -> {label} (score: {score:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ NLP error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("数据智能分析平台 - 系统测试")
    print("=" * 60)
    
    results = []
    results.append(("Import Test", test_imports()))
    results.append(("Model Test", test_models()))
    results.append(("Security Test", test_security()))
    results.append(("NLP Test", test_nlp()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20s}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("\n运行以下命令启动服务器:")
        print("  python app.py")
        print("  或")
        print("  ./start_server.sh")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

import unittest
import os
import hashlib
from database import init_db, get_db_connection
from auth import signup_user, login_user, hash_password
from pace_model import calculate_quiz_score, get_pace_category, update_learning_pace
from quiz_generator import generate_quiz_offline, generate_materials_offline

class TestAdaptiveLearningSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize database for testing (seeding occurs automatically if empty)
        init_db()
        # Clear test records from previous runs
        conn = get_db_connection()
        cursor = conn.cursor()
        test_users = ('unittest_user', 'rolling_tester')
        cursor.execute("DELETE FROM quiz_history WHERE username IN (?, ?)", test_users)
        cursor.execute("DELETE FROM topics WHERE username IN (?, ?)", test_users)
        cursor.execute("DELETE FROM interactions WHERE username IN (?, ?)", test_users)
        cursor.execute("DELETE FROM users WHERE username IN (?, ?)", test_users)
        conn.commit()
        conn.close()
        
    def test_password_hashing(self):
        """Verify that password hashing functions properly."""
        password = "testpassword123"
        hashed = hash_password(password)
        expected = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.assertEqual(hashed, expected)

    def test_signup_and_login(self):
        """Verify signup works and login checks credentials correctly."""
        username = "unittest_user"
        password = "unitpass123"
        
        # Test clean signup
        success = signup_user(username, password)
        # It could return False if user already exists from a previous run, 
        # so let's check credentials instead
        login_ok = login_user(username, password)
        self.assertTrue(login_ok)
        
        # Verify invalid password fails
        login_fail = login_user(username, "wrongpassword")
        self.assertFalse(login_fail)

    def test_quiz_score_calculation(self):
        """Verify that combined accuracy and speed score works as expected."""
        # 100% Accuracy, very fast (5s per question) -> Should get perfect 100 score
        score_fast = calculate_quiz_score(1.0, 50.0, 10)
        self.assertEqual(score_fast, 100.0)
        
        # 100% Accuracy, slow (60s per question) -> Should get less than 100
        score_slow = calculate_quiz_score(1.0, 600.0, 10)
        self.assertTrue(score_slow < 100.0)
        self.assertTrue(score_slow > 70.0) # Accuracy alone contributes 70
        
        # 0% Accuracy -> Score should be speed score only
        score_zero_acc = calculate_quiz_score(0.0, 10.0, 10)
        self.assertEqual(score_zero_acc, 30.0) # Speed score max is 30

    def test_pace_category_mapping(self):
        """Verify score ranges map to appropriate learning speeds."""
        self.assertEqual(get_pace_category(10.0), "Super Slow")
        self.assertEqual(get_pace_category(35.0), "Slow")
        self.assertEqual(get_pace_category(50.0), "Medium")
        self.assertEqual(get_pace_category(65.0), "Average")
        self.assertEqual(get_pace_category(80.0), "Fast")
        self.assertEqual(get_pace_category(95.0), "Super Fast")

    def test_rolling_pace_update(self):
        """Verify that multiple quiz completions update learning pace incrementally."""
        username = "rolling_tester"
        topic = "Machine Learning"
        
        # Signup tester
        signup_user(username, "password")
        
        # First attempt: 5/10 (50% accuracy), 200s total (20s/q)
        # Expected quiz score: 0.5 * 70 + speed_score
        # speed_score for 20s/q is: 30 * (1 - (20 - 10)/80) = 30 * 7/8 = 26.25
        # Total quiz score = 35 + 26.25 = 61.25
        pace_cat_1, pace_score_1, attempt_1 = update_learning_pace(
            username, topic, score=5, total_questions=10, time_taken_sec=200.0
        )
        self.assertEqual(attempt_1, 1)
        self.assertAlmostEqual(pace_score_1, 61.25)
        self.assertEqual(pace_cat_1, "Average")
        
        # Second attempt: High score 9/10, fast (10s/q)
        # Quiz score: 90% accuracy -> 63 pts. Speed -> 30 pts. Total = 93 pts.
        # Rolling formula:
        # P_new = 0.4 * 93 + 0.6 * 61.25 + 0.1 * (93 - 61.25)
        # P_new = 37.2 + 36.75 + 3.175 = 77.125
        pace_cat_2, pace_score_2, attempt_2 = update_learning_pace(
            username, topic, score=9, total_questions=10, time_taken_sec=100.0
        )
        self.assertEqual(attempt_2, 2)
        self.assertAlmostEqual(pace_score_2, 77.125)
        self.assertEqual(pace_cat_2, "Fast")

    def test_offline_quiz_generator(self):
        """Verify the template fallback generates valid quiz items."""
        quiz = generate_quiz_offline("Machine Learning", "Slow")
        self.assertEqual(len(quiz), 10)
        for item in quiz:
            self.assertIn("question", item)
            self.assertEqual(len(item["options"]), 4)
            self.assertTrue(0 <= item["correct_idx"] < 4)
            
    def test_offline_materials_generator(self):
        """Verify the template fallback generates educational recommendations."""
        materials = generate_materials_offline("Python Programming", "Fast")
        self.assertIn("summary", materials)
        self.assertEqual(len(materials["articles"]), 2)
        self.assertEqual(len(materials["videos"]), 2)

if __name__ == "__main__":
    unittest.main()

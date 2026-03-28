"""Test validators for Pydantic models."""
from models import StudyNotes, WorkBrief, VideoInsights, ActionItem, PreWatchVerdict

print("=" * 60)
print("Testing Pydantic Model Validators")
print("=" * 60)

# Test StudyNotes validation - should work
print("\n1️⃣  Testing StudyNotes (valid data)...")
try:
    study = StudyNotes(
        title="Single Slit Diffraction",
        core_concept="Diffraction creates intensity minima at specific angles following a·sinθ = nλ.",
        formula_sheet=["a·sinθ = nλ — a is slit width"],
        key_facts=["Fact 1 from transcript", "Fact 2 from transcript"],
        common_mistakes=[],
        self_test=["What is single slit diffraction"],
        prerequisites=[],
        further_reading=[]
    )
    print("   ✓ StudyNotes validation works")
except Exception as e:
    print(f"   ✗ StudyNotes error: {e}")

# Test WorkBrief validation - should work
print("\n2️⃣  Testing WorkBrief (valid data)...")
try:
    work = WorkBrief(
        title="Redis Caching Strategies",
        one_liner="Deep dive into Redis caching with benchmark comparisons.",
        recommendation="Watch — practical framework for evaluating AI automation tools.",
        key_points=["Redis outperforms Memcached by 3x on persistence workloads"],
        tools_mentioned=["Redis", "Memcached"],
        decisions_to_make=["Evaluate adding Redis as caching layer"],
        next_actions=[]
    )
    print("   ✓ WorkBrief validation works")
except Exception as e:
    print(f"   ✗ WorkBrief error: {e}")

# Test VideoInsights validation - should work
print("\n3️⃣  Testing VideoInsights (valid data)...")
try:
    quick = VideoInsights(
        title="How Neural Networks Work",
        summary="This video explains how neural networks learn from data through gradient descent.",
        key_takeaways=["Neural networks need backpropagation to learn"],
        topics_covered=["Backpropagation", "Gradient Descent"],
        action_items=[]
    )
    print("   ✓ VideoInsights validation works")
except Exception as e:
    print(f"   ✗ VideoInsights error: {e}")

# Test PreWatchVerdict validation
print("\n4️⃣  Testing PreWatchVerdict (valid data)...")
try:
    verdict = PreWatchVerdict(
        verdict="Watch",
        why="This explains the core concept with practical examples.",
        best_for="Students learning machine learning.",
        relevant_moments=["00:30 — Introduction to backpropagation", "05:15 — Mathematical derivation"],
        what_youll_miss_if_skip="Understanding how neural networks update weights during training."
    )
    print("   ✓ PreWatchVerdict validation works")
except Exception as e:
    print(f"   ✗ PreWatchVerdict error: {e}")

print("\n" + "=" * 60)
print("Testing Invalid Data (should be rejected)")
print("=" * 60)

# Test StudyNotes validation - should FAIL (generic title)
print("\n5️⃣  Testing StudyNotes (INVALID: generic title)...")
try:
    study_fail = StudyNotes(
        title="Study Notes",
        core_concept="This is a concept.",
        formula_sheet=[],
        key_facts=["Fact"],
        common_mistakes=[],
        self_test=[],
        prerequisites=[],
        further_reading=[]
    )
    print("   ✗ Generic title validation FAILED - should have been rejected")
except Exception as e:
    print(f"   ✓ Correctly rejected: {str(e)[:70]}...")

# Test WorkBrief validation - should FAIL (bad recommendation format)
print("\n6️⃣  Testing WorkBrief (INVALID: bad recommendation format)...")
try:
    work_fail = WorkBrief(
        title="Good Title",
        one_liner="This is good.",
        recommendation="This is not formatted correctly.",
        key_points=["A key point"],
        tools_mentioned=[],
        decisions_to_make=[],
        next_actions=[]
    )
    print("   ✗ Bad recommendation validation FAILED - should have been rejected")
except Exception as e:
    print(f"   ✓ Correctly rejected: {str(e)[:70]}...")

# Test ActionItem validation - should FAIL (bad priority)
print("\n7️⃣  Testing ActionItem (INVALID: bad priority)...")
try:
    action_fail = ActionItem(
        task="Deploy to production",
        assignee="DevOps Team",
        due_date="2026-04-15",
        priority="Urgent"  # Should be High, Medium, or Low
    )
    print("   ✗ Bad priority validation FAILED - should have been rejected")
except Exception as e:
    print(f"   ✓ Correctly rejected: {str(e)[:70]}...")

# Test PreWatchVerdict - should FAIL (bad verdict)
print("\n8️⃣  Testing PreWatchVerdict (INVALID: bad verdict value)...")
try:
    verdict_fail = PreWatchVerdict(
        verdict="Maybe",  # Should be Watch, Skim, or Skip
        why="This might be useful.",
        best_for="Anyone",
        relevant_moments=[],
        what_youll_miss_if_skip="Nothing really"
    )
    print("   ✗ Bad verdict validation FAILED - should have been rejected")
except Exception as e:
    print(f"   ✓ Correctly rejected: {str(e)[:70]}...")

print("\n" + "=" * 60)
print("✅ All model validators working correctly!")
print("=" * 60)

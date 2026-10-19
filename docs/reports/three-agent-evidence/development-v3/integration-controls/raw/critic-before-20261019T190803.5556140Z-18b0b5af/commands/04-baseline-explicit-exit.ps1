python -B -c "import sys,unittest; sys.path.insert(0,'scripts'); result=unittest.TextTestRunner(stream=sys.stdout,verbosity=1).run(unittest.defaultTestLoader.discover('scripts',pattern='test_build_manifest.py')); print('UNITTEST_SUCCESS=' + str(result.wasSuccessful())); sys.exit(0 if result.wasSuccessful() else 1)"
$pythonExit = $LASTEXITCODE
Write-Output "PYTHON_EXIT_CODE=$pythonExit"
exit $pythonExit

rm -rf build

pyv="$(python -V 2>&1)"
echo "Packaging with $pyv"
# Build dependencies:
pip install -r requirements.txt --target ./build
# Have to specify this platform to get proper libpg binding in lambda:
pip install \
    --platform manylinux2014_x86_64 \
    --target=./build \
    --implementation cp \
    --python 3.9 \
    --only-binary=:all: --upgrade \
    'psycopg[binary,pool]'

# Move required application files into build:
cp *.py build/.
cp -R lib build/.
cp -R config build/.

cd build/
zip -qr build.zip *

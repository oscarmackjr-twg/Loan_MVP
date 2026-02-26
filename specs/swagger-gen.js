// swagger-gen.js
const path = require('path');
const glob = require('glob');
const fs = require('fs');

// --- Resolve all paths relative to the PROJECT ROOT, not the script location ---
// Adjust this if your project root is elsewhere relative to this script
const PROJECT_ROOT = path.resolve(__dirname, '..');

const OPENAPI_VERSION = '3.0.0';
const swaggerAutogen = require('swagger-autogen')({ openapi: OPENAPI_VERSION });

const doc = {
  info: {
    title: 'My API',
    version: '1.0.0',
    description: 'Auto-generated API specification',
  },
  host: 'localhost:3000',
  basePath: '/',
  schemes: ['http'],
  consumes: ['application/json'],
  produces: ['application/json'],
  components: {
    schemas: {},
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      },
    },
  },
};

const outputFile = path.resolve(__dirname, 'openapi-spec.json');

// --- Step 1: Discover where your route files actually live ---
// Common Express project structures — adjust or extend as needed
const candidatePatterns = [
  'src/routes/**/*.js',
  'src/routes/**/*.ts',
  'routes/**/*.js',
  'routes/**/*.ts',
  'src/api/**/*.js',
  'src/api/**/*.ts',
  'api/**/*.js',
  'server/routes/**/*.js',
  'app/routes/**/*.js',
];

console.log(`Project root: ${PROJECT_ROOT}\n`);

// --- Step 2: Also try to find the Express app entry point ---
// swagger-autogen works best when pointed at the file that mounts routes on the app
const appCandidates = [
  'src/app.js', 'src/app.ts',
  'src/server.js', 'src/server.ts',
  'src/index.js', 'src/index.ts',
  'app.js', 'server.js', 'index.js',
];

let appEntryPoint = null;
for (const candidate of appCandidates) {
  const fullPath = path.join(PROJECT_ROOT, candidate);
  if (fs.existsSync(fullPath)) {
    appEntryPoint = fullPath;
    console.log(`Found app entry point: ${candidate}`);
    break;
  }
}

// --- Step 3: Resolve route files using glob from project root ---
let endpointsFiles = [];
for (const pattern of candidatePatterns) {
  const absolutePattern = path.join(PROJECT_ROOT, pattern);
  const matched = glob.sync(absolutePattern);
  if (matched.length > 0) {
    console.log(`Pattern "${pattern}" matched ${matched.length} file(s)`);
    endpointsFiles = endpointsFiles.concat(matched);
  }
}

// Deduplicate
endpointsFiles = [...new Set(endpointsFiles)];

// --- Step 4: If no route files found, help the developer diagnose ---
if (endpointsFiles.length === 0) {
  console.error('\nERROR: No route files found.\n');
  console.error('Scanning project for Express route patterns...\n');

  // Search for any JS/TS file containing router or app.get/post/put/delete
  const allJsFiles = glob.sync(path.join(PROJECT_ROOT, '**/*.{js,ts}'), {
    ignore: ['**/node_modules/**', '**/dist/**', '**/build/**', '**/.next/**'],
  });

  const routeIndicators = [
    /express\.Router\(\)/,
    /router\.(get|post|put|delete|patch)\(/,
    /app\.(get|post|put|delete|patch)\(/,
  ];

  const filesWithRoutes = allJsFiles.filter((file) => {
    try {
      const content = fs.readFileSync(file, 'utf8');
      return routeIndicators.some((pattern) => pattern.test(content));
    } catch {
      return false;
    }
  });

  if (filesWithRoutes.length > 0) {
    console.log('Found files containing Express route definitions:\n');
    filesWithRoutes.forEach((f) => {
      console.log(`  ${path.relative(PROJECT_ROOT, f)}`);
    });
    console.log('\nUpdate the candidatePatterns array in swagger-gen.js to include these paths.');
    console.log('Or pass them directly via command line:\n');
    console.log('  node swagger-gen.js --routes "src/controllers/**/*.js"\n');
  } else {
    console.error('No files with Express route patterns found in the project.');
    console.error('Verify this is the correct project root:', PROJECT_ROOT);
    console.error('\nDirectory contents:');
    fs.readdirSync(PROJECT_ROOT).forEach((item) => {
      const stat = fs.statSync(path.join(PROJECT_ROOT, item));
      console.error(`  ${stat.isDirectory() ? '[DIR] ' : '      '}${item}`);
    });
  }

  process.exit(1);
}

// --- Step 5: Report what was found and generate ---
console.log(`\nTotal route files to process: ${endpointsFiles.length}`);
endpointsFiles.forEach((f) => console.log(`  - ${path.relative(PROJECT_ROOT, f)}`));
console.log('');

(async () => {
  try {
    const result = await swaggerAutogen(outputFile, endpointsFiles, doc);

    if (result?.success) {
      const pathCount = Object.keys(result.data?.paths || {}).length;
      console.log(`OpenAPI spec generated: ${outputFile}`);
      console.log(`  Endpoints detected: ${pathCount}`);
      console.log(`  Output format: OpenAPI ${OPENAPI_VERSION}`);

      if (pathCount === 0) {
        console.warn('\nWARNING: Spec generated but zero endpoints detected.');
        console.warn('This usually means swagger-autogen could not parse the route patterns.');
        console.warn('Consider pointing endpointsFiles at your app entry point instead:');
        if (appEntryPoint) {
          console.warn(`  Try: endpointsFiles = ['${appEntryPoint}']`);
        }
        console.warn('Or add #swagger comments to your route handlers.');
      }
    } else {
      console.error('Spec generation reported failure.');
      process.exit(1);
    }
  } catch (err) {
    console.error('Fatal error:', err.message);
    process.exit(1);
  }
})();

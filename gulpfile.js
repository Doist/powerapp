var path = require('path');
var gulp = require('gulp');
var changed = require('gulp-changed');
var gulpif = require('gulp-if');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var uglifycss = require('gulp-uglifycss');
var beautify = require('gulp-beautify');
var autoprefixer = require('gulp-autoprefixer');
var sourcemaps = require('gulp-sourcemaps');
var less = require('gulp-less');
var rename = require('gulp-rename');


var config = {
    release: process.env.RELEASE !== undefined,
    materialize_path: 'node_modules/materialize-css/bin',
    less_path: 'powerapp/project_static/less',

    js_files: [
        "node_modules/jquery/dist/jquery.js",
        "node_modules/materialize-css/bin/materialize.js",
        "powerapp/project_static/js_src/*.js"
    ],
    less_files: [
        "powerapp/project_static/less/*.less"
    ],
    font_files: [
        "node_modules/materialize-css/font/**/*"
    ]
};


// Take css file from materialize, rename it to less and add to "our library"
gulp.task('lessify-materialize', function() {
    var target = path.join(config.less_path, "lib");
    return gulp.src(path.join(config.materialize_path, "*.css"))
        .pipe(changed(target, {extension: ".less"}))
        .pipe(rename({extname: ".less"}))
        .pipe(gulp.dest(target))
});


// Compile all less files to one big CSS
gulp.task('styles', ['lessify-materialize'], function() {
    gulp.src(path.join(config.less_path, "*.less"))
        .pipe(less({paths: [config.less_path]}))
        .pipe(gulpif(config.release, uglifycss()))
        .pipe(autoprefixer())
        .pipe(concat("style.css"))
        .pipe(gulp.dest("powerapp/project_static/css"));
});


gulp.task('scripts', function() {
    gulp.src(config.js_files)
        .pipe(gulpif(config.release, sourcemaps.init()))
        .pipe(gulpif(config.release, uglify(), beautify()))
        .pipe(concat("script.js"))
        .pipe(gulpif(config.release, sourcemaps.write()))
        .pipe(gulp.dest("powerapp/project_static/js"));
});


gulp.task('fonts', function() {
    gulp.src(config.font_files)
        .pipe(gulp.dest("powerapp/project_static/font"));
});

gulp.task('default', ['scripts', 'styles', 'fonts']);

gulp.task('watch', ['default'], function() {
    gulp.watch([
        config.js_files, config.less_files, config.font_files
    ], ['default']);
});

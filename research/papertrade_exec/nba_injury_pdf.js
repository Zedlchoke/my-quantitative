// G7-i: macOS native PDFKit text extraction via osascript JXA.
// No Python PDF dependency and no network access in this helper.
function run(argv) {
    ObjC.import("PDFKit");
    if (argv.length !== 1) throw new Error("expected one local PDF path");
    var url = $.NSURL.fileURLWithPath(argv[0]);
    var document = $.PDFDocument.alloc.initWithURL(url);
    if (!document) throw new Error("PDFKit could not open report");
    return ObjC.unwrap(document.string);
}

import { Download, FileText } from "lucide-react";

export function ExportButtons({ onExport, disabled, exporting }) {
  return (
    <div className="export-buttons">
      <button
        type="button"
        className="secondary-button"
        onClick={() => onExport("pdf")}
        disabled={disabled || exporting}
      >
        <Download size={17} />
        Export PDF
      </button>
      <button
        type="button"
        className="secondary-button"
        onClick={() => onExport("docx")}
        disabled={disabled || exporting}
      >
        <FileText size={17} />
        Export DOCX
      </button>
    </div>
  );
}


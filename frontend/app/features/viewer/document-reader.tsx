'use client';
/* eslint-disable react/react-compiler, next/no-img-element */
import { useEffect, useRef, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  FileText,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import type { PDFDocumentProxy } from 'pdfjs-dist';
// Vite's ?url imports are build assets, not JavaScript module exports.
// eslint-disable-next-line import/default
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import type { DocumentVersion } from '../../domain-types';
import { getFile, request } from '../../workspace-api';

type Content = {
  note?: string;
  sections: { title: string; text?: string; rows?: string[][] }[];
};
export function DocumentReader({ version }: { version?: DocumentVersion }) {
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(1);
  const [picture, setPicture] = useState('');
  const [content, setContent] = useState<Content | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pageText, setPageText] = useState('');
  const canvas = useRef<HTMLCanvasElement>(null);
  const surface = useRef<HTMLDivElement>(null);
  const [availableWidth, setAvailableWidth] = useState(600);
  useEffect(() => {
    if (!surface.current) return;
    const observer = new ResizeObserver((entries) => {
      setAvailableWidth(Math.max(120, entries[0].contentRect.width));
    });
    observer.observe(surface.current);
    return () => observer.disconnect();
  }, [version]);
  useEffect(() => {
    const controller = new AbortController();
    let url = '';
    let dispose: (() => void) | undefined;
    setPdf(null);
    setContent(null);
    setPicture('');
    setError('');
    setPage(1);
    setZoom(1);
    if (!version) return () => controller.abort();
    setLoading(true);
    void (async () => {
      try {
        const extension = version.file_name.split('.').pop()?.toLowerCase();
        if (extension === 'pdf') {
          const library = await import('pdfjs-dist');
          library.GlobalWorkerOptions.workerSrc = workerUrl;
          const blob = await getFile(version.view_url, controller.signal);
          if (controller.signal.aborted) return;
          const task = library.getDocument({ data: await blob.arrayBuffer() });
          dispose = () => {
            void task.destroy();
          };
          const document = await task.promise;
          if (!controller.signal.aborted) setPdf(document);
          else dispose();
        } else if (
          ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(extension || '')
        ) {
          const blob = await getFile(version.view_url, controller.signal);
          if (!controller.signal.aborted) {
            url = URL.createObjectURL(blob);
            setPicture(url);
          }
        } else {
          const kind = version.view_url.includes('/research/')
            ? 'research'
            : 'project';
          const data = await request<Content>(
            '/viewer/' + kind + '/' + version.id,
            { signal: controller.signal },
          );
          if (!controller.signal.aborted) setContent(data);
        }
      } catch (reason) {
        if (!controller.signal.aborted)
          setError(
            reason instanceof Error
              ? reason.message
              : 'Unable to preview this file.',
          );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();
    return () => {
      controller.abort();
      dispose?.();
      if (url) URL.revokeObjectURL(url);
    };
  }, [version]);
  useEffect(() => {
    if (!pdf || !canvas.current) return;
    let cancelled = false;
    let task: { cancel: () => void; promise: Promise<void> } | undefined;
    void (async () => {
      try {
        const sheet = await pdf.getPage(page);
        if (cancelled || !canvas.current) return;
        const base = sheet.getViewport({ scale: 1 });
        const cssScale = Math.min(availableWidth / base.width, 1.6) * zoom;
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
        const viewport = sheet.getViewport({ scale: cssScale * pixelRatio });
        const element = canvas.current;
        const context = element.getContext('2d');
        if (!context) return;
        element.width = viewport.width;
        element.height = viewport.height;
        element.style.width = viewport.width / pixelRatio + 'px';
        element.style.height = viewport.height / pixelRatio + 'px';
        task = sheet.render({
          canvas: element,
          canvasContext: context,
          viewport,
        });
        await task.promise;
        const text = await sheet.getTextContent();
        if (!cancelled)
          setPageText(
            text.items.map((item) => ('str' in item ? item.str : '')).join(' '),
          );
      } catch (reason) {
        if (!cancelled)
          setError(
            reason instanceof Error
              ? reason.message
              : 'Page could not be rendered.',
          );
      }
    })();
    return () => {
      cancelled = true;
      task?.cancel();
    };
  }, [pdf, page, zoom, availableWidth]);
  if (!version)
    return (
      <div className="reader-empty">
        <FileText size={42} />
        <h3>Your document opens here</h3>
        <p>Select a file to read it without leaving Verdant.</p>
      </div>
    );
  return (
    <section className="reader" aria-label="Document reader">
      <div className="reader-toolbar">
        <span title={version.file_name}>{version.file_name}</span>
        {pdf && (
          <div className="reader-controls">
            <button
              aria-label="Previous page"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft size={17} />
            </button>
            <span>
              Page {page} of {pdf.numPages}
            </span>
            <button
              aria-label="Next page"
              disabled={page === pdf.numPages}
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight size={17} />
            </button>
            <button
              aria-label="Zoom out"
              disabled={zoom <= 0.5}
              onClick={() => setZoom(zoom - 0.25)}
            >
              <ZoomOut size={17} />
            </button>
            <span>{Math.round(zoom * 100)}%</span>
            <button
              aria-label="Zoom in"
              disabled={zoom >= 2}
              onClick={() => setZoom(zoom + 0.25)}
            >
              <ZoomIn size={17} />
            </button>
          </div>
        )}
      </div>
      <div className="reader-surface" ref={surface}>
        {loading && <output>Opening document…</output>}
        {error && (
          <div className="notice error" role="alert">
            {error}
          </div>
        )}
        {pdf && (
          <>
            <canvas ref={canvas} aria-label={'PDF page ' + page} />
            <p className="sr-only">{pageText}</p>
          </>
        )}
        {/* Authenticated blob URLs cannot use the server-side image optimizer. */}
        {/* eslint-disable-next-line next/no-img-element */}
        {picture && (
          <img
            className="image-preview"
            src={picture}
            alt={version.file_name}
          />
        )}
        {content && (
          <article className="office-preview">
            <p className="preview-note">{content.note}</p>
            {content.sections.map((section, i) => (
              <section key={i}>
                <h3>{section.title}</h3>
                {section.text && <pre>{section.text}</pre>}
                {section.rows && (
                  <div className="table-scroll">
                    <table>
                      <tbody>
                        {section.rows.map((row, index) => (
                          <tr key={index}>
                            {row.map((cell, c) => (
                              <td key={c}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            ))}
          </article>
        )}
      </div>
    </section>
  );
}

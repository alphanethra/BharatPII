async function scanFile(file) {
  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch("http://127.0.0.1:8000/scan", {
    method: "POST",
    body: fd
  });

  return await res.json();
}

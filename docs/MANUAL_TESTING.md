# SourceLens manual testing checklist

Run these checks after installing the project and adding a valid OpenAI API key to `.env`.

## Fresh installation

- [ ] Unzip the project into a new folder.
- [ ] Run `./setup_macos.sh`.
- [ ] Add a valid `OPENAI_API_KEY` value to `.env`.
- [ ] Run `./run_macos.sh`.
- [ ] Confirm that the SourceLens page opens without import errors.

## PDF collection behavior

- [ ] Upload one text-based PDF and build the document index.
- [ ] Confirm that the sidebar shows the PDF filename, readable-page count, and searchable-passage count.
- [ ] Upload multiple text-based PDFs and build a new index.
- [ ] Confirm that all readable PDF names appear in the indexed-document list.
- [ ] Upload one valid PDF together with a corrupted `.pdf` file.
- [ ] Confirm that the valid file is indexed and the damaged file is reported clearly.
- [ ] Upload an image-only scanned PDF.
- [ ] Confirm that SourceLens explains that it could not extract searchable text.
- [ ] Upload a password-protected PDF.
- [ ] Confirm that SourceLens skips it and displays a warning.

## Conversation behavior

- [ ] Ask a question before building an index.
- [ ] Confirm that SourceLens asks you to build a document index first.
- [ ] Submit a valid question after indexing.
- [ ] Confirm that an assistant answer appears.
- [ ] Expand **Referenced passages** under the answer.
- [ ] Confirm that each passage shows the source document, page number, chunk number, and similarity score.
- [ ] Ask a follow-up question that depends on the previous answer.
- [ ] Confirm that the reply remains grounded in the uploaded PDFs.
- [ ] Ask a question that is not answered by the PDFs.
- [ ] Confirm that the answer states that supported information could not be found instead of fabricating an answer.
- [ ] Attempt to submit a blank question.
- [ ] Confirm that the interface prevents submission or rejects the blank input.

## Session controls

- [ ] Select **Start New Conversation**.
- [ ] Confirm that the messages disappear but the indexed-document summary remains.
- [ ] Ask a new question and confirm that the existing index still works.
- [ ] Select **Remove Collection**.
- [ ] Confirm that the messages, indexed summary, and uploaded-file selection are cleared.

## Final inspection

- [ ] Run `pytest -q` and confirm that all automated tests pass.
- [ ] Confirm that `.env` is excluded from Git with `git check-ignore .env` after initializing a repository.
- [ ] Confirm that the README setup instructions match the actual commands.
- [ ] Confirm that there are no unused source files or broken imports.

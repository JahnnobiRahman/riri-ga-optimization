# MDPI Template Update Checklist
**Date**: August 8, 2026  
**Purpose**: Update from March 2024 template to July 2026 template

---

## Step 1: Backup Current Files ✓

```bash
cd ~/Desktop/python/allcode/projects/mdpi/paper
cp -r Definitions/ Definitions_backup_2024_03_20/
```

**Verify backup:**
```bash
ls -la Definitions_backup_2024_03_20/
# Should show: mdpi.cls, mdpi.bst, logo files, etc.
```

---

## Step 2: Download Fresh MDPI Template

**URL**: https://res.mdpi.com/data/MDPI_template_ACS.zip?v=20260728

**Why ACS style?** Your paper uses numbered citations `[1], [2]`, which is the ACS/numbered style. Mathematics journal uses this format.

**Alternative if link fails**: Go to https://www.mdpi.com/authors/latex and download "Mathematics Template (ACS citation style)"

---

## Step 3: Extract and Replace Definitions/

```bash
# Extract the downloaded zip
unzip ~/Downloads/MDPI_template_ACS.zip -d ~/Downloads/mdpi_template_new/

# Navigate to extracted template
cd ~/Downloads/mdpi_template_new/

# Copy the new Definitions/ folder to your paper directory
# (This will overwrite - that's why we backed up!)
cp -r Definitions/ ~/Desktop/python/allcode/projects/mdpi/paper/

# Verify the new files have correct dates
ls -la ~/Desktop/python/allcode/projects/mdpi/paper/Definitions/
# mdpi.cls should show a 2026 date (July/August)
```

---

## Step 4: Verify Template Files Updated

```bash
cd ~/Desktop/python/allcode/projects/mdpi/paper/Definitions
head -30 mdpi.cls | grep "ProvidesClass\|Version"
# Should show: 2024 or later (not 20/03/2024)

head -30 mdpi.bst | grep "Version"
# Should show: something newer than 0.99b (8-Dec-10)
```

---

## Step 5: Full LaTeX Compile Sequence

```bash
cd ~/Desktop/python/allcode/projects/mdpi/paper

# Clean previous build artifacts
rm -f main.aux main.bbl main.blg main.log main.out

# Full compile sequence
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

**Watch for errors** - if you see the `\@LN@column` error again, the new template didn't fix it. Jump to "Troubleshooting" below.

---

## Step 6: Verification Checklist

Open the generated `main.pdf` and verify:

### ✅ Line Numbers
- [ ] Line numbers appear in the left margin
- [ ] Line numbers run continuously throughout the paper
- [ ] Line numbers don't interfere with text or figures

### ✅ Citations Format
- [ ] All citations render as `[1]`, `[2]`, `[3]` etc. (numbered)
- [ ] NOT as `(Author, Year)` or similar
- [ ] No `[?]` placeholders (all \cite{} keys resolved)

### ✅ References Section
- [ ] References section appears at end
- [ ] All 29+ references listed and numbered
- [ ] Format looks consistent (authors, title, journal, year, DOI)

### ✅ No New Errors
Check the compile log:
```bash
grep -i "error\|warning" main.log | head -20
```
- [ ] No new "undefined control sequence" errors
- [ ] No "undefined reference" warnings
- [ ] Overfull/underfull hbox warnings are OK (cosmetic)

### ✅ Content Intact
Spot-check a few sections:
- [ ] Title, authors, affiliations render correctly
- [ ] Abstract and keywords present
- [ ] All figures appear
- [ ] All tables appear
- [ ] Appendices present

---

## Step 7: Check Specific Known Issues

### Check 1: Cleveref Still Works
Your paper uses `\cref{}` for cross-references. Verify:
```bash
grep -n "Figure~\\\\ref" main.tex
# Should return nothing (you use \cref{}, not \ref{})
```

Open the PDF and click on a few cross-references (e.g., "Figure 3", "Table 5") - they should be hyperlinked and jump to the correct location.

### Check 2: Bengali Font Still Loads
```bash
grep -n "bengalifont\|Noto Serif Bengali" main.tex
```
Spot-check Table 8 or any Bengali text in the PDF - should render correctly, not as boxes/question marks.

---

## Troubleshooting

### If `\@LN@column` error persists:

1. **Check TeX Live version:**
   ```bash
   xelatex --version
   # Should be TeX Live 2024 or later
   ```

2. **Update lineno package:**
   ```bash
   tlmgr update lineno
   tlmgr update cleveref
   ```

3. **Check mdpi.cls actually updated:**
   ```bash
   head -5 Definitions/mdpi.cls
   # Should NOT say "20/03/2024"
   ```

4. **If still failing**: The new template may have introduced a different issue. Send me:
   - The exact error message from the compile log
   - Output of: `grep "ProvidesClass" Definitions/mdpi.cls`
   - Output of: `xelatex --version`

### If citations render as (Author, Year):

You downloaded the wrong template variant. You need **ACS** (numbered), not APA or Chicago (author-year).

1. Delete Definitions/ 
2. Restore backup: `cp -r Definitions_backup_2024_03_20/ Definitions/`
3. Download the **ACS** zip specifically
4. Retry Step 3

### If compile succeeds but PDF looks broken:

Compare to backup PDF:
```bash
open main.pdf
open ~/Desktop/python/allcode/projects/mdpi/paper_backup_2024/main.pdf
```

If the new one is clearly worse (missing content, weird formatting), restore backup and report the issue:
```bash
cp -r Definitions_backup_2024_03_20/ Definitions/
```

---

## Success Criteria

Template update is complete when ALL of the following are true:

✅ `xelatex main.tex` compiles with exit code 0  
✅ Line numbers appear in PDF  
✅ No `\@LN@column` error in log  
✅ Citations render as `[1]`, `[2]` etc.  
✅ All 29+ references appear correctly  
✅ Figures, tables, appendices intact  
✅ Bengali text renders correctly  
✅ Cross-references (\\cref) still hyperlinked  

---

## After Successful Update

1. **Delete the backup** (only after confirming everything works):
   ```bash
   rm -rf Definitions_backup_2024_03_20/
   ```

2. **Commit the changes** (if using git):
   ```bash
   git add Definitions/ main.tex
   git commit -m "Update MDPI template to 2026-07-28 version, re-enable submit option"
   ```

3. **Generate final PDF for submission:**
   ```bash
   # One more clean compile
   rm -f main.aux main.bbl main.blg main.out
   xelatex main.tex && bibtex main && xelatex main.tex && xelatex main.tex
   
   # Verify file size reasonable (should be 2-5 MB)
   ls -lh main.pdf
   ```

---

## Notes

- **Your main.tex is untouched** - only Definitions/ was replaced
- **Your references.bib is untouched** - all citations should still work
- **Your figures/ folder is untouched** - all images should still appear
- The `submit` option has been re-enabled in main.tex (line 11)
- If any issues arise, you have a clean backup in Definitions_backup_2024_03_20/

**Date of this update**: August 8, 2026  
**Your current template**: March 20, 2024  
**Target template**: July 28, 2026  
**Gap**: 16+ months

from typing import List
from idseq_dag.util.parsing import HitSummaryMergedReader
from idseq_dag.engine.pipeline_step import PipelineStep
import idseq_dag.util.lineage as lineage

from idseq_dag.util.dict import open_file_db_by_extension
from idseq_dag.util import fasta


def _get_valid_lineage(hits_by_read_id, lineage_map, read_id: str) -> List[str]:
    # If the read aligned to something, then it would be present in the
    # summary file for count type, and correspondingly in hits_by_read_id
    # even if the hits disagree so much that the
    # "valid_hits" entry is just ("-1", "-1"). If the read didn't align
    # to anything, we also represent that with ("-1", "-1"). This ("-1",
    # "-1") gets translated to NULL_LINEAGE.
    hit_taxid, hit_level = hits_by_read_id.get(read_id, (-1, -1))
    hit_lineage = lineage_map.get(str(hit_taxid), lineage.NULL_LINEAGE)
    return lineage.validate_taxid_lineage(hit_lineage, hit_taxid, hit_level)


def generate_taxid_fasta(
    input_fa_name: str,
    nt_hit_summary_path: str,
    nr_hit_summary_path: str,
    lineage_db_path: str,
    output_fasta_path: str,
):
    with open(nt_hit_summary_path) as nt_hit_summary_f, open(nr_hit_summary_path) as nr_hit_summary_f:
        nr_hits_by_read_id = {row["read_id"]: (row["taxid"], row["level"]) for row in HitSummaryMergedReader(nr_hit_summary_f)}
        nt_hits_by_read_id = {row["read_id"]: (row["taxid"], row["level"]) for row in HitSummaryMergedReader(nt_hit_summary_f)}

    with open(output_fasta_path, "w") as output_fa, \
            open_file_db_by_extension(lineage_db_path, "lll") as lineage_map:  # noqa
        for read in fasta.iterator(input_fa_name):
            # Example read_id: "NR::NT:CP010376.2:NB501961:14:HM7TLBGX2:1:23109
            # :12720:8743/2"
            # Translate the read information into our custom format with fake
            # taxids at non-specific hit levels.
            # TODO: (tmorse) fasta parsing
            annotated_read_id = read.header.lstrip('>')
            read_id = annotated_read_id.split(":", 4)[-1]

            nr_taxid_species, nr_taxid_genus, nr_taxid_family = _get_valid_lineage(
                nr_hits_by_read_id, lineage_map, read_id)
            nt_taxid_species, nt_taxid_genus, nt_taxid_family = _get_valid_lineage(
                nt_hits_by_read_id, lineage_map, read_id)

            fields = ["family_nr", nr_taxid_family, "family_nt", nt_taxid_family]
            fields += ["genus_nr", nr_taxid_genus, "genus_nt", nt_taxid_genus]
            fields += ["species_nr", nr_taxid_species, "species_nt", nt_taxid_species]
            fields += [annotated_read_id]
            new_read_name = ('>' + ':'.join(fields) + '\n')

            output_fa.write(new_read_name)
            output_fa.write(read.sequence + "\n")


class PipelineStepGenerateTaxidFasta(PipelineStep):
    """Generate taxid FASTA from hit summaries. Intermediate conversion step
    that includes handling of non-specific hits with artificial tax_ids.
    """

    def run(self):
        input_fa_name = self.input_files_local[0][0]
        if len(self.input_files_local) > 1:
            input_fa_name = self.input_files_local[0][0]
            nt_hit_summary_path, nr_hit_summary_path = self.input_files_local[1][2], self.input_files_local[2][2]
        else:
            # This is used in `short-read-mngs/experimental.wdl`
            input_fa_name = self.input_files_local[0][0]
            nt_hit_summary_path, nr_hit_summary_path = self.input_files_local[0][1], self.input_files_local[0][2]

        generate_taxid_fasta(
            input_fa_name,
            nt_hit_summary_path,
            nr_hit_summary_path,
            self.additional_files["lineage_db"],
            self.output_files_local()[0],
        )

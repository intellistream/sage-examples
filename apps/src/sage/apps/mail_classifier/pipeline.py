from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import MailCategoryClassifier, MailParser, MailPriorityScorer, MailSink, MailSource


def run_mail_classifier_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("mail_classifier")
    (
        env.from_batch(MailSource, input_file=input_file)
        .map(MailParser)
        .map(MailCategoryClassifier)
        .map(MailPriorityScorer)
        .sink(MailSink, output_file=output_file)
    )
    env.submit(autostop=True)

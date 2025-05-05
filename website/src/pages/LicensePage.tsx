import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const LicensePage: React.FC = () => {
  useEffect(() => {
    document.title = 'License - baid';
  }, []);

  return (
    <section className="pt-20 pb-20">
      <div className="container-custom">
        <div className="mb-10">
          <Link to="/" className="btn btn-ghost inline-flex items-center">
            <ArrowLeft className="mr-2 h-5 w-5" />
            Back to Home
          </Link>
        </div>
        
        <h1 className="text-3xl md:text-5xl font-semibold mb-8 text-center">Terms of Service - Hosted</h1>

        <div className="prose prose-lg max-w-none">
          <h2 className="text-2xl font-black mb-2">Baid Plugin License Agreement</h2>
          <p className="text-md text-surface-300 mb-6">
            Last updated: May 1, 2025
          </p>

          <p className="mb-6">
            Thank you for choosing to be part of our community at Baid ("Company," "we," "us," or "our"). We are
            committed to protecting your personal information and your right to privacy. If you have any questions or
            concerns about this privacy notice or our practices with regard to your personal information, please contact
            us at <a href="mailto:baid@beskar.tech">Baid@Beskar</a>.
          </p>

          <h3 className="text-xl font-medium mb-3">PLEASE READ THE FOLLOWING TERMS CAREFULLY:</h3>
          <p className="mb-4">
            BY CLICKING "I ACCEPT," OR BY DOWNLOADING, INSTALLING, OR OTHERWISE ACCESSING OR USING THE SERVICE, YOU
            AGREE THAT YOU HAVE READ AND UNDERSTOOD, AND, AS A CONDITION TO YOUR USE OF THE SERVICE, YOU AGREE TO BE
            BOUND BY, THE FOLLOWING TERMS AND CONDITIONS, INCLUDING BAID'S PRIVACY POLICY (TOGETHER, THESE "TERMS"). If
            you are not eligible, or do not agree to the Terms, then you do not have our permission to use the Service.
            YOUR USE OF THE SERVICE, AND BAID'S PROVISION OF THE SERVICE TO YOU, CONSTITUTES AN AGREEMENT BY BAID AND BY
            YOU TO BE BOUND BY THESE TERMS.
          </p>

          <p className="mb-4">
            ARBITRATION NOTICE. Except for certain kinds of disputes described in Section 20, you agree that disputes
            arising under these Terms will be resolved by binding, individual arbitration, and BY ACCEPTING THESE TERMS,
            YOU AND BAID ARE EACH WAIVING THE RIGHT TO A TRIAL BY JURY OR TO PARTICIPATE IN ANY CLASS ACTION OR
            REPRESENTATIVE PROCEEDING.
          </p>

          <h3 className="text-xl font-medium mb-3">1. Service Overview</h3>
          <p className="mb-4">
            Our Baid platform offers a suite of coding tools driven by artificial intelligence to help developers write
            code more easily and efficiently (the "Platform") and can provide suggested code, outputs or other functions
            (each, a "Suggestion"). We also offer a limited version of the Platform through our website to anyone, with
            or without an account.
          </p>

          <h3 className="text-xl font-medium mb-3">2. Eligibility</h3>
          <p className="mb-4">
            You must be at least 13 years old to use the Service. By agreeing to these Terms, you represent and warrant
            to us that: (a) you are at least 13 years old; (b) you have not previously been suspended or removed from
            the Service; and (c) your registration and your use of the Service is in compliance with any and all
            applicable laws and regulations. If you are an entity, organization, or company, the individual accepting
            these Terms on your behalf represents and warrants that they have authority to bind you to these Terms and
            you agree to be bound by these Terms.
          </p>

          <h3 className="text-xl font-medium mb-3">3. Accounts and Registration</h3>
          <p className="mb-4">
            To access most features of the Service, you must register for an account. When you register for an account,
            you may be required to provide us with some information about yourself, such as your name, email address, or
            other contact information. You agree that the information you provide to us is accurate, complete, and not
            misleading, and that you will keep it accurate and up to date at all times. When you register, you will be
            asked to create a password. You are solely responsible for maintaining the confidentiality of your account
            and password, and you accept responsibility for all activities that occur under your account.
          </p>

          <h3 className="text-xl font-medium mb-3">4. Beta or Trial Versions</h3>
          <p className="mb-4">
            Baid may from time to time offer trial or beta models or versions or features of the Service (each, a "Beta
            Service"). Baid will determine, at its sole discretion, the availability, duration (the "Trial Period"),
            features, and components of each Beta Service. ANY BETA SERVICE IS PROVIDED "AS IS" WITHOUT ANY WARRANTIES.
          </p>

          <h3 className="text-xl font-medium mb-3">5. General Payment Terms</h3>
          <p className="mb-4">
            We offer a paid version of this Individual license, which includes enhanced features. Before you pay any
            fees, you will have an opportunity to review and accept the fees that you will be charged. All fees are in
            U.S. Dollars and are non-refundable, except as required by law.
          </p>

          <h3 className="text-xl font-medium mb-3">6. Licenses</h3>
          <h4 className="text-xl font-medium mb-3">6.1. Limited License</h4>
          <p className="mb-4">
            Subject to your complete and ongoing compliance with these Terms, and the payment of the applicable Fee (for
            Pro Users), Baid grants you, solely for your personal use, a limited, non-exclusive, non-transferable,
            non-sublicensable, revocable license to: (a) install and use one object code copy of any downloadable
            application that we provide to you, on a device that you own or control; and (b) access and use the Service.
          </p>

          <h4 className="text-xl font-medium mb-3">6.2. License Restrictions</h4>
          <p className="mb-4">
            Except and solely to the extent such a restriction is impermissible under applicable law, you may not: (a)
            reproduce, distribute, publicly display, publicly perform, or create derivative works of the Service; (b)
            make modifications to the Service; or (c) interfere with or circumvent any feature of the Service, including
            any security or access control mechanism.
          </p>

          <h4 className="text-xl font-medium mb-3">6.3. Feedback</h4>
          <p className="mb-4">
            The Service is owned and operated by Baid. All materials included in the Service are the property of Baid or
            its third-party licensors. Except as expressly authorized by Baid, you may not make use of the Materials.
            There are no implied licenses in these Terms and Baid reserves all rights to the Materials not granted
            expressly in these Terms.We respect and appreciate the thoughts and comments from our users. If you choose
            to provide input and suggestions regarding existing functionalities, problems with or proposed modifications
            or improvements to the Service ("Feedback"), then you hereby grant Baid an unrestricted, perpetual,
            irrevocable, non-exclusive, fully-paid, royalty-free right and license to exploit the Feedback in any manner
            and for any purpose, including to improve the Service and create other products and services.
          </p>

          <h3 className="text-xl font-medium mb-3">7. Ownership; Proprietary Rights</h3>
          <p className="mb-6">
            The Service is owned and operated by Baid. All materials included in the Service are the property of Baid or
            its third-party licensors. Except as expressly authorized by Baid, you may not make use of the Materials.
            There are no implied licenses in these Terms and Baid reserves all rights to the Materials not granted
            expressly in these Terms.
          </p>

          <h3 className="text-xl font-medium mb-3">8. User Content</h3>
          <h4 className="text-xl font-medium mb-3">8.1. User Content Generally</h4>
          <p className="mb-4">
            Certain features of the Service may permit users to submit, upload, publish, broadcast, or otherwise
            transmit ("Post") content to the Service, including data, text, and any other works ("User Content"). You
            retain any copyright and other proprietary rights that you may hold in the User Content that you Post to the
            Service, subject to the licenses granted in these Terms.
          </p>

          <h4 className="text-xl font-medium mb-3">8.2. Use of User Content</h4>
          <p className="mb-4">
            By Posting User Content to or via the Service, you authorize us to use it to provide the Service and
            Suggestions to you.
          </p>

          <h3 className="text-xl font-medium mb-3">9. Prohibited Conduct</h3>
          <p className="mb-4">
            BY USING THE SERVICE, YOU AGREE NOT TO:

            <li>use the Service for any illegal purpose or in violation of any applicable law;</li>
            <li>harass, threaten, demean, embarrass, bully, or otherwise harm any other user of the Service;</li>
            <li>violate, encourage others to violate, or provide instructions on how to violate, any right of a third
              party;
            </li>
            <li>interfere with security-related features of the Service;</li>
            <li>interfere with the operation of the Service or any user's enjoyment of the Service;</li>
            <li>perform any fraudulent activity including impersonating any person or entity;</li>
            <li>sell or otherwise transfer the access granted under these Terms;</li>
            <li>attempt to do any of the acts described in this Section or assist or permit any person in engaging in
              any of the acts described in this Section.
            </li>
          </p>

          <h3 className="text-xl font-medium mb-3">10. Intellectual Property Rights Protection</h3>

          <h4 className="text-xl font-medium mb-3">10.1. Respect of Third Party Rights</h4>
          <p className="mb-4">
            Baid respects the intellectual property rights of others, takes the protection of intellectual property
            rights very seriously, and asks users of the Service to do the same. Infringing activity will not be
            tolerated on or through the Service.
          </p>

          <h4 className="text-xl font-medium mb-3">10.2. DMCA Notification</h4>
          <p className="mb-4">
            We comply with the provisions of the Digital Millennium Copyright Act applicable to Internet service
            providers (17 U.S.C. § 512, as amended). If you have an intellectual property rights-related complaint about
            any material on the Service, you may contact our Designated Agent at the following address:
          </p>
          <p className="mb-4">
            Baid<br/>
            Attn: Legal Department (IP Notification)<br/>
            No 202, YD Lotus Pond, 3rd Main Road, OMBR Layout, Bangalore, Karnataka - 560043, India.<br/>
            Email: <a href="mailto:dmca@beskar.tech">dmca@beskar.tech</a>
          </p>

          <h3 className="text-xl font-medium mb-3">11. Disclaimers; No Warranties</h3>
          <p className="mb-4">
            THE SERVICE AND ALL MATERIALS AND CONTENT AVAILABLE THROUGH THE SERVICE, INCLUDING SUGGESTIONS, ARE PROVIDED
            "AS IS" AND ON AN "AS AVAILABLE" BASIS. BAID DISCLAIMS ALL WARRANTIES OF ANY KIND, WHETHER EXPRESS OR
            IMPLIED, RELATING TO THE SERVICE AND ALL MATERIALS AND CONTENT AVAILABLE THROUGH THE SERVICE.
          </p>

          <h3 className="text-xl font-medium mb-3">12. Limitation of Liability</h3>
          <p className="mb-4">
            TO THE FULLEST EXTENT PERMITTED BY LAW, IN NO EVENT WILL BAID BE LIABLE TO YOU FOR ANY INDIRECT, INCIDENTAL,
            SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES ARISING OUT OF OR RELATING TO YOUR ACCESS TO OR USE OF, OR YOUR
            INABILITY TO ACCESS OR USE, THE SERVICE OR ANY MATERIALS OR CONTENT ON THE SERVICE.
          </p>

          <h3 className="text-xl font-medium mb-3">13. Dispute Resolution and Arbitration</h3>
          <p className="mb-4">
            Except as described below, you and Baid agree that every dispute arising in connection with these Terms, the
            Service, or communications from us will be resolved through binding arbitration.
          </p>

          <h3 className="text-xl font-medium mb-3">14. Miscellaneous</h3>

          <h4 className="text-xl font-medium mb-3">14.1. Governing Law</h4>
          <p className="mb-4">
            These Terms are governed by the laws of [Your Jurisdiction] without regard to conflict of law principles.
          </p>

          <h4 className="text-xl font-medium mb-3">14.2. Contact Information</h4>
          <p className="mb-4">
            The Service is offered by Baid, located at [Your Address]. You may contact us by sending correspondence to
            that address or by emailing us at <a href="mailto:contact@baid.com">contact@baid.com</a>.
          </p>

          <h4 className="text-xl font-medium mb-3">14.3. Force Majeure</h4>
          <p className="mb-4">
            Neither party is liable for any delay or failure to perform any obligation under these Terms (except for a
            failure to pay fees) due to events beyond its reasonable control.
          </p>

          <h4 className="text-xl font-medium mb-3">14.4. Export Control</h4>
          <p className="mb-4">
            You acknowledge and understand that the Service and Suggestions are subject to U.S. export control and
            sanctions laws and regulations.
          </p>

          <p className="mb-4">© 2025 Baid. All rights reserved.</p>
        </div>
      </div>
    </section>
  );
};

export default LicensePage;
